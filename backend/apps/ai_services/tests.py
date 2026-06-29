import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from unittest.mock import patch

import fitz
from django.test import SimpleTestCase
from docx import Document

from .resume_preprocessor import (
    cleanup_punctuation,
    coerce_text,
    normalize_tokens,
    normalize_whitespace,
    preprocess_for_matching,
    preprocess_for_semantic_matching,
    safe_lower,
)
from .resume_text_extractor import ResumeTextExtractionError, extract_resume_text
from .resume_screening import (
    calculate_education_score,
    calculate_experience_score,
    calculate_skill_score,
    extract_education,
    extract_experience,
)
from .scoring import calculate_final_score, calculate_score_breakdown
from .exceptions import AIServiceUnavailable
from .semantic_matcher import semantic_similarity
from .skill_extractor import (
    _load_spacy_model,
    extract_skill_labels,
    extract_skills,
    get_skill_display_labels,
    normalize_skill_key,
    normalize_text,
)


class ResumeTextExtractorTests(SimpleTestCase):
    def test_extract_resume_text_from_pdf(self):
        with TemporaryDirectory() as temporary_directory:
            file_path = Path(temporary_directory) / 'resume.pdf'
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), 'Python developer')
            document.save(file_path)
            document.close()

            self.assertEqual(extract_resume_text(file_path), 'Python developer')

    def test_extract_resume_text_from_docx_includes_paragraphs_and_table_cells(self):
        with TemporaryDirectory() as temporary_directory:
            file_path = Path(temporary_directory) / 'resume.docx'
            document = Document()
            document.add_paragraph('Backend engineer')
            table = document.add_table(rows=1, cols=1)
            table.cell(0, 0).text = 'Django'
            document.save(file_path)

            self.assertEqual(extract_resume_text(file_path), 'Backend engineer\nDjango')

    def test_extract_resume_text_rejects_unsupported_file_type(self):
        with self.assertRaisesMessage(ResumeTextExtractionError, 'Unsupported resume file type: .txt'):
            extract_resume_text('resume.txt')

    def test_extract_resume_text_rejects_missing_local_file(self):
        with self.assertRaisesMessage(ResumeTextExtractionError, 'Resume file does not exist'):
            extract_resume_text('missing-resume.pdf')


class ResumePreprocessorTests(SimpleTestCase):
    def test_coerce_text_handles_none_strings_and_non_string_input(self):
        self.assertEqual(coerce_text(None), '')
        self.assertEqual(coerce_text('Resume'), 'Resume')
        self.assertEqual(coerce_text(2026), '2026')

    def test_normalize_whitespace_collapses_repeated_whitespace(self):
        self.assertEqual(normalize_whitespace('  Python\n\t  Django   developer  '), 'Python Django developer')

    def test_safe_lower_lowercases_without_other_cleanup(self):
        self.assertEqual(safe_lower('  React.JS!  '), '  react.js!  ')

    def test_cleanup_punctuation_preserves_common_skill_symbols_by_default(self):
        self.assertEqual(cleanup_punctuation('C++, C#, React.js, Node.js!'), 'C++ C# React.js Node.js ')

    def test_normalize_tokens_can_remove_skill_symbols_when_requested(self):
        self.assertEqual(
            normalize_tokens('C++, C#, React.js', preserve_skill_symbols=False),
            'c c react js',
        )

    def test_preprocess_for_matching_returns_safe_normalized_matching_text(self):
        self.assertEqual(preprocess_for_matching('  Python,   React.js!  '), 'python react.js')

    def test_preprocess_for_semantic_matching_keeps_normalized_copy_only(self):
        original_text = '  Backend   Engineer: Python/Django  '

        self.assertEqual(preprocess_for_semantic_matching(original_text), 'backend engineer python django')
        self.assertEqual(original_text, '  Backend   Engineer: Python/Django  ')


class _FakeStrings:
    def __getitem__(self, match_id):
        return match_id


class _FakeVocab:
    strings = _FakeStrings()


class _FakeNLP:
    vocab = _FakeVocab()

    def __call__(self, text):
        return text

    def make_doc(self, text):
        return text


class _FakePhraseMatcher:
    def __init__(self, _vocab, attr=None):
        self.patterns_by_skill = {}

    def add(self, skill_key, patterns):
        self.patterns_by_skill[skill_key] = patterns

    def __call__(self, doc):
        matches = []
        for skill_key, patterns in self.patterns_by_skill.items():
            if any(_fake_contains_alias(doc, pattern) for pattern in patterns):
                matches.append((skill_key, 0, 1))
        return matches


def _fake_contains_alias(normalized_text, normalized_alias):
    pattern = rf'(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])'
    return bool(re.search(pattern, normalized_text))


class SkillExtractorTests(SimpleTestCase):
    def test_normalize_text_lowercases_and_removes_extra_punctuation(self):
        self.assertEqual(normalize_text('  Python,   React.js!  '), 'python react.js')

    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_extract_skills_normalizes_aliases_and_returns_canonical_names(self, _mock_spacy_model, _mock_phrase_matcher_class):
        resume_text = 'Built RESTful APIs with Python, Django, ReactJS, PostgreSQL, AWS, and C++.'

        self.assertEqual(
            extract_skills(resume_text),
            ['aws', 'c++', 'django', 'postgresql', 'python', 'react', 'rest api'],
        )

    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_extract_skills_does_not_match_alias_inside_another_word(self, _mock_spacy_model, _mock_phrase_matcher_class):
        self.assertEqual(extract_skills('Enjoys javascript.', {'java': ('java',)}), [])

    def test_extract_skills_accepts_an_empty_custom_dictionary(self):
        self.assertEqual(extract_skills('Python', {}), [])

    @patch('apps.ai_services.skill_extractor._load_spacy_model', side_effect=AIServiceUnavailable('spaCy unavailable'))
    def test_extract_skills_raises_when_spacy_unavailable(self, _mock_spacy_model):
        with self.assertRaises(AIServiceUnavailable):
            extract_skills('Built RESTful APIs with py, js, nodejs, postgres, and reactjs.')

    def test_load_spacy_model_raises_when_spacy_dependency_import_fails(self):
        _load_spacy_model.cache_clear()
        self.addCleanup(_load_spacy_model.cache_clear)

        with (
            patch('apps.ai_services.skill_extractor.importlib.util.find_spec', return_value=object()),
            patch(
                'apps.ai_services.skill_extractor.importlib.import_module',
                side_effect=ModuleNotFoundError('click'),
            ) as mock_import_module,
        ):
            with self.assertRaises(AIServiceUnavailable):
                _load_spacy_model()

        mock_import_module.assert_called_once_with('spacy')

    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_extract_skill_labels_uses_spacy_matches(self, _mock_spacy_model, _mock_phrase_matcher_class):
        with patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher), patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP()):
            self.assertEqual(extract_skill_labels('py js reactjs nodejs postgres'), [
                'JavaScript',
                'Node.js',
                'PostgreSQL',
                'Python',
                'React',
            ])

    def test_normalize_skill_key_maps_aliases_to_internal_keys(self):
        self.assertEqual(normalize_skill_key('py'), 'python')
        self.assertEqual(normalize_skill_key('js'), 'javascript')
        self.assertEqual(normalize_skill_key('reactjs'), 'react')
        self.assertEqual(normalize_skill_key('nodejs'), 'node.js')
        self.assertEqual(normalize_skill_key('postgres'), 'postgresql')

    def test_skill_display_labels_are_additive_and_canonical(self):
        self.assertEqual(
            get_skill_display_labels(['python', 'javascript', 'react', 'node.js', 'postgresql']),
            ['Python', 'JavaScript', 'React', 'Node.js', 'PostgreSQL'],
        )
        with patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher), patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP()):
            self.assertEqual(extract_skill_labels('py js reactjs nodejs postgres'), [
                'JavaScript',
                'Node.js',
                'PostgreSQL',
                'Python',
                'React',
            ])

    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_extract_skills_uses_spacy_phrase_matcher_when_available(
        self, _mock_spacy_model, _mock_phrase_matcher_class
    ):
        self.assertEqual(
            extract_skills('Experience with PY, ReactJS, NodeJS, and Postgres.'),
            ['node.js', 'postgresql', 'python', 'react'],
        )


class SemanticMatcherTests(SimpleTestCase):
    @patch('apps.ai_services.semantic_matcher._get_model', side_effect=ModuleNotFoundError)
    def test_semantic_similarity_raises_when_dependency_is_unavailable(self, _mock_model):
        with self.assertRaises(AIServiceUnavailable):
            semantic_similarity('Python Django developer', 'Django Python engineer')

    @patch('apps.ai_services.semantic_matcher._get_model', side_effect=OSError('offline model download failed'))
    def test_semantic_similarity_raises_when_model_loading_fails(self, _mock_model):
        with self.assertRaises(AIServiceUnavailable):
            semantic_similarity('Python Django developer', 'Django Python engineer')

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_raises_when_encoding_fails(self, mock_get_model):
        mock_get_model.return_value.encode.side_effect = RuntimeError('tensor execution failed')

        with self.assertRaises(AIServiceUnavailable):
            semantic_similarity('Python Django developer', 'Django Python engineer')

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_raises_when_tensor_handling_fails(self, mock_get_model):
        mock_get_model.return_value.encode.return_value = []

        with self.assertRaises(AIServiceUnavailable):
            semantic_similarity('Python Django developer', 'Django Python engineer')

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_uses_model_embeddings_when_dependency_is_available(self, mock_get_model):
        mock_get_model.return_value.encode.return_value = [_Vector(0.75), _Vector(0.75)]

        self.assertEqual(semantic_similarity('  Python,   developer!  ', 'Backend\nengineer'), 75.0)
        mock_get_model.return_value.encode.assert_called_once_with(
            ['python developer', 'backend engineer'],
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_normalizes_model_scores_to_zero_to_one_hundred(self, mock_get_model):
        mock_get_model.return_value.encode.return_value = [_Vector(1.5), _Vector(1.5)]
        self.assertEqual(semantic_similarity('Python', 'Python'), 100.0)

        mock_get_model.return_value.encode.return_value = [_Vector(-0.25), _Vector(-0.25)]
        self.assertEqual(semantic_similarity('Python', 'Python'), 0.0)

    def test_semantic_similarity_returns_zero_for_blank_input(self):
        self.assertEqual(semantic_similarity('', 'Backend engineer'), 0.0)
        self.assertEqual(semantic_similarity('Python developer', '   '), 0.0)


class _Vector:
    def __init__(self, similarity):
        self.similarity = similarity

    def __matmul__(self, _other):
        return self

    def item(self):
        return self.similarity


class ScoringTests(SimpleTestCase):
    def test_calculate_final_score_uses_required_weights(self):
        self.assertEqual(calculate_final_score(80, 70, 60, 50), 70.0)

    def test_calculate_final_score_matches_exact_required_formula(self):
        semantic_score = 82.5
        skill_score = 75.0
        experience_score = 60.0
        education_score = 80.0

        expected = round(
            (0.4 * semantic_score)
            + (0.3 * skill_score)
            + (0.2 * experience_score)
            + (0.1 * education_score),
            2,
        )

        self.assertEqual(
            calculate_final_score(semantic_score, skill_score, experience_score, education_score),
            expected,
        )

    def test_calculate_score_breakdown_returns_components_and_final_score(self):
        self.assertEqual(
            calculate_score_breakdown(80, 70, 60, 50),
            {
                'semantic_score': 80,
                'skill_score': 70,
                'experience_score': 60,
                'education_score': 50,
                'final_score': 70.0,
            },
        )

    def test_calculate_final_score_rejects_out_of_range_component(self):
        with self.assertRaisesMessage(ValueError, 'skill_score must be between 0 and 100'):
            calculate_final_score(80, 101, 60, 50)


class ResumeScreeningScoreComponentTests(SimpleTestCase):
    def test_extract_experience_uses_highest_explicit_year_value(self):
        result = extract_experience('2 years support and 5+ yrs development')

        self.assertEqual(result['years'], 5.0)
        self.assertIn('years', result)

    def test_extract_experience_preprocesses_text_before_matching(self):
        result = extract_experience('Worked with Python.\n  3+     YRS!!!')

        self.assertEqual(result['years'], 3.0)
        self.assertIn('3+ YRS', result['raw_mentions'])

    def test_extract_experience_detects_roles_companies_and_internships(self):
        result = extract_experience(
            'Software engineer at ABC Company. Worked as developer. Internship at Beta Labs.'
        )

        self.assertEqual(result['years'], 0.0)
        self.assertIn('software engineer', result['roles'])
        self.assertIn('developer', result['roles'])
        self.assertIn('intern', result['roles'])
        self.assertIn('ABC Company', result['companies'])
        self.assertIn('Beta Labs', result['companies'])
        self.assertIn('Internship at Beta Labs', result['internships'])
        self.assertIn('Software engineer at ABC Company', result['matched_phrases'])

    def test_extract_experience_keeps_old_expected_keys_while_returning_richer_object(self):
        result = extract_experience('5 yrs as a backend developer')

        self.assertIn('years', result)
        self.assertIn('roles', result)
        self.assertIn('companies', result)
        self.assertIn('internships', result)
        self.assertIn('matched_phrases', result)
        self.assertIn('raw_mentions', result)

    def test_extract_education_uses_highest_mentioned_level(self):
        result = extract_education("Bachelor's degree and master's degree")

        self.assertEqual(result['level'], 'master')
        self.assertEqual(result['level_label'], 'Master')

    def test_extract_education_preprocesses_text_before_matching(self):
        result = extract_education('Completed B.Sc, then MBA.')

        self.assertEqual(result['level'], 'master')
        self.assertIn('Bachelor', result['matched_keywords'])
        self.assertIn('Master', result['matched_keywords'])

    def test_extract_education_detects_all_supported_levels(self):
        examples = {
            'secondary': 'High School certificate',
            'diploma': 'Diploma in Information Technology',
            'associate': 'Associate Degree in Computer Science',
            'bachelor': 'Bachelor Degree in Software Engineering',
            'master': 'Master of Computer Science',
            'doctorate': 'PhD in Software Engineering',
        }

        for expected_level, text in examples.items():
            with self.subTest(expected_level=expected_level):
                self.assertEqual(extract_education(text)['level'], expected_level)

    def test_extract_education_detects_fields_of_study(self):
        result = extract_education(
            'Bachelor Degree in Computer Science and Diploma in Information Technology. '
            'Completed Software Engineering capstone.'
        )

        self.assertEqual(result['level'], 'bachelor')
        self.assertEqual(
            result['fields_of_study'],
            ['Computer Science', 'Software Engineering', 'Information Technology'],
        )
        self.assertIn('Degree', result['matched_keywords'])
        self.assertIn('Computer Science', result['raw_mentions'])

    def test_extract_education_keeps_old_expected_keys_while_returning_richer_object(self):
        result = extract_education('Bachelor Degree in Computer Science')

        self.assertIn('level', result)
        self.assertIn('level_label', result)
        self.assertIn('fields_of_study', result)
        self.assertIn('matched_keywords', result)
        self.assertIn('raw_mentions', result)

    def test_skill_score_calculates_required_skill_coverage(self):
        self.assertEqual(calculate_skill_score(['django', 'python'], ['django', 'python', 'sql']), 66.67)

    def test_skill_score_uses_requirement_weight_scores_when_available(self):
        skill_requirements = [
            {'skills': ['python'], 'weight_score': 80.0},
            {'skills': ['react'], 'weight_score': 20.0},
        ]

        self.assertEqual(calculate_skill_score(['python'], ['python', 'react'], skill_requirements), 80.0)

    def test_experience_score_is_capped_at_one_hundred(self):
        self.assertEqual(calculate_experience_score({'years': 5.0}, {'years': 3.0}), 100.0)

    def test_education_score_is_zero_when_required_level_is_missing_from_resume(self):
        self.assertEqual(calculate_education_score({'level': None}, {'level': 'bachelor'}), 0.0)


class LinkedInProfileImporterTests(SimpleTestCase):
    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_linkedin_profile_fixture_is_parsed_into_expected_sections(self, _mock_spacy_model, _mock_phrase_matcher_class):
        from .linkedin_profile_importer import build_linkedin_profile_import

        fixture_dir = Path(__file__).resolve().parents[1] / 'users' / 'test_fixtures'
        raw_text = (fixture_dir / 'linkedin_profile_sample_raw.txt').read_text()
        expected = json.loads((fixture_dir / 'linkedin_profile_sample_expected.json').read_text())

        parsed = build_linkedin_profile_import(raw_text)

        self.assertEqual(parsed['full_name'], expected['full_name'])
        self.assertEqual(parsed['headline'], expected['headline'])
        self.assertEqual(parsed['location'], expected['location'])
        self.assertEqual(parsed['linkedin_url'], expected['linkedin_url'])
        self.assertEqual(parsed['summary'], expected['summary'])
        self.assertEqual(parsed['skills'][:len(expected['skills'])], expected['skills'])
        for expected_skill in ['Java', 'Kubernetes', 'AWS']:
            self.assertIn(expected_skill, parsed['skills'])
        self.assertEqual(parsed['certifications'], expected['certifications'])
        self.assertEqual(parsed['experience'], expected['experience'])
        self.assertEqual(parsed['education'], expected['education'])


    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_linkedin_profile_parser_merges_sidebar_and_headline_skills(self, _mock_spacy_model, _mock_phrase_matcher_class):
        from .linkedin_profile_importer import build_linkedin_profile_import

        parsed = build_linkedin_profile_import(
            'Contact\nwww.linkedin.com/in/dev-profile\nTop Skills\nTechnical Standards\n'
            'Dev Candidate\nSoftware Engineer | Java • Kubernetes • AWS |\nMalaysia\nSummary\n'
            'Building backend services.\nExperience\nExample Co\nEngineer\n'
            'January 2024 - Present (6 months)'
        )

        self.assertEqual(parsed['skills'][0], 'Technical Standards')
        self.assertIn('Java', parsed['skills'])
        self.assertIn('Kubernetes', parsed['skills'])
        self.assertIn('AWS', parsed['skills'])

    @patch('apps.ai_services.skill_extractor._get_phrase_matcher_class', return_value=_FakePhraseMatcher)
    @patch('apps.ai_services.skill_extractor._load_spacy_model', return_value=_FakeNLP())
    def test_linkedin_profile_parser_handles_missing_optional_sections(self, _mock_spacy_model, _mock_phrase_matcher_class):
        from .linkedin_profile_importer import build_linkedin_profile_import

        parsed = build_linkedin_profile_import('Alex Applicant\nBackend Developer\nMalaysia\nExperience\nExample Co\nEngineer\nJanuary 2024 - Present (6 months)')

        self.assertEqual(parsed['full_name'], 'Alex Applicant')
        self.assertEqual(parsed['headline'], 'Backend Developer')
        self.assertEqual(parsed['location'], 'Malaysia')
        self.assertEqual(parsed['skills'], [])
        self.assertEqual(parsed['certifications'], [])
        self.assertEqual(parsed['education'], [])
        self.assertEqual(parsed['experience'][0]['company_name'], 'Example Co')



class ResumeMatchModelTests(SimpleTestCase):
    def test_ml_screening_requires_trained_artifact(self):
        from .ml.resume_matcher import build_ml_screening_result

        with self.assertRaises(AIServiceUnavailable):
            build_ml_screening_result(
                semantic_score=80,
                skill_score=75,
                experience_score=70,
                education_score=100,
                rule_based_score=78,
                matched_skills=['python', 'django'],
                missing_skills=['postgresql'],
                experience_gap={'gap_years': 0},
                education_gap={'gap_levels': 0},
                resume_text='Python Django developer with five years experience',
                job_text='Backend developer requiring Python Django PostgreSQL',
            )

    def test_score_to_label_uses_expected_match_bands(self):
        from .ml.resume_matcher import score_to_label

        self.assertEqual(score_to_label(90), 'strong_match')
        self.assertEqual(score_to_label(70), 'moderate_match')
        self.assertEqual(score_to_label(50), 'weak_match')
        self.assertEqual(score_to_label(30), 'not_suitable')
