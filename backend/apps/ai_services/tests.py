from pathlib import Path
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
from .semantic_matcher import fallback_semantic_similarity, semantic_similarity
from .skill_extractor import extract_skills, normalize_text


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


class SkillExtractorTests(SimpleTestCase):
    def test_normalize_text_lowercases_and_removes_extra_punctuation(self):
        self.assertEqual(normalize_text('  Python,   React.js!  '), 'python react.js')

    def test_extract_skills_normalizes_aliases_and_returns_canonical_names(self):
        resume_text = 'Built RESTful APIs with Python, Django, ReactJS, PostgreSQL, AWS, and C++.'

        self.assertEqual(
            extract_skills(resume_text),
            ['aws', 'c++', 'django', 'postgresql', 'python', 'react', 'rest api'],
        )

    def test_extract_skills_does_not_match_alias_inside_another_word(self):
        self.assertEqual(extract_skills('Enjoys javascript.', {'java': ('java',)}), [])

    def test_extract_skills_accepts_an_empty_custom_dictionary(self):
        self.assertEqual(extract_skills('Python', {}), [])


class SemanticMatcherTests(SimpleTestCase):
    @patch('apps.ai_services.semantic_matcher._get_model', side_effect=ModuleNotFoundError)
    def test_semantic_similarity_uses_deterministic_fallback_when_dependency_is_unavailable(self, _mock_model):
        self.assertEqual(semantic_similarity('Python Django developer', 'Django Python engineer', fallback_score=62), 50.0)

    @patch('apps.ai_services.semantic_matcher._get_model', side_effect=OSError('offline model download failed'))
    def test_semantic_similarity_uses_deterministic_fallback_when_model_loading_fails(self, _mock_model):
        self.assertEqual(semantic_similarity('Python Django developer', 'Django Python engineer'), 50.0)

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_uses_deterministic_fallback_when_encoding_fails(self, mock_get_model):
        mock_get_model.return_value.encode.side_effect = RuntimeError('tensor execution failed')

        self.assertEqual(semantic_similarity('Python Django developer', 'Django Python engineer'), 50.0)

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_uses_deterministic_fallback_when_tensor_handling_fails(self, mock_get_model):
        mock_get_model.return_value.encode.return_value = []

        self.assertEqual(semantic_similarity('Python Django developer', 'Django Python engineer'), 50.0)

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

    def test_semantic_similarity_rejects_out_of_range_fallback_score_for_api_compatibility(self):
        with self.assertRaisesMessage(ValueError, 'fallback_score must be between 0 and 100'):
            semantic_similarity('Python', 'Backend engineer', fallback_score=101)

    def test_fallback_semantic_similarity_scores_related_text_higher_than_unrelated_text(self):
        related_score = fallback_semantic_similarity(
            'Python Django REST API backend developer',
            'Backend engineer building Python Django APIs',
        )
        unrelated_score = fallback_semantic_similarity(
            'Python Django REST API backend developer',
            'Payroll benefits compliance specialist',
        )

        self.assertGreater(related_score, unrelated_score)


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

    def test_experience_score_is_capped_at_one_hundred(self):
        self.assertEqual(calculate_experience_score({'years': 5.0}, {'years': 3.0}), 100.0)

    def test_education_score_is_zero_when_required_level_is_missing_from_resume(self):
        self.assertEqual(calculate_education_score({'level': None}, {'level': 'bachelor'}), 0.0)
