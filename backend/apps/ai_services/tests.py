from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import fitz
from django.test import SimpleTestCase
from docx import Document

from .resume_text_extractor import ResumeTextExtractionError, extract_resume_text
from .resume_screening import (
    calculate_education_score,
    calculate_experience_score,
    calculate_skill_score,
    extract_education,
    extract_experience,
)
from .scoring import calculate_final_score, calculate_score_breakdown
from .semantic_matcher import semantic_similarity
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
    def test_semantic_similarity_returns_mock_score_when_dependency_is_unavailable(self, _mock_model):
        self.assertEqual(semantic_similarity('Python developer', 'Backend engineer', fallback_score=62), 62.0)

    @patch('apps.ai_services.semantic_matcher._get_model')
    def test_semantic_similarity_uses_model_embeddings_when_dependency_is_available(self, mock_get_model):
        mock_get_model.return_value.encode.return_value = [_Vector(), _Vector()]

        self.assertEqual(semantic_similarity('Python developer', 'Backend engineer'), 75.0)

    def test_semantic_similarity_returns_zero_for_blank_input(self):
        self.assertEqual(semantic_similarity('', 'Backend engineer'), 0.0)

    def test_semantic_similarity_rejects_out_of_range_fallback_score(self):
        with self.assertRaisesMessage(ValueError, 'fallback_score must be between 0 and 100'):
            semantic_similarity('Python', 'Backend engineer', fallback_score=101)


class _Vector:
    def __matmul__(self, _other):
        return self

    def item(self):
        return 0.75


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
        self.assertEqual(extract_experience('2 years support and 5+ yrs development'), {'years': 5.0})

    def test_extract_education_uses_highest_mentioned_level(self):
        self.assertEqual(extract_education("Bachelor's degree and master's degree"), {'level': 'master'})

    def test_skill_score_calculates_required_skill_coverage(self):
        self.assertEqual(calculate_skill_score(['django', 'python'], ['django', 'python', 'sql']), 66.67)

    def test_experience_score_is_capped_at_one_hundred(self):
        self.assertEqual(calculate_experience_score({'years': 5.0}, {'years': 3.0}), 100.0)

    def test_education_score_is_zero_when_required_level_is_missing_from_resume(self):
        self.assertEqual(calculate_education_score({'level': None}, {'level': 'bachelor'}), 0.0)
