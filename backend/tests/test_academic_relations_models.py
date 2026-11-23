
import unittest
from dataclasses import fields
from datetime import date, time

from app.models.curriculum import Curriculum
from app.models.curriculum_course import CurriculumCourse
from app.models.class_section import ClassSection
from app.models.enrollment import Enrollment


class AcademicRelationsModelsTestCase(unittest.TestCase):

    def test_curriculum_fields_match_data_model(self):
        expected = [
            "curriculumId",
            "majorId",
            "curriculumName",
            "academicYear",
        ]

        self.assertEqual(
            [f.name for f in fields(Curriculum)],
            expected,
        )

    def test_curriculum_references_major(self):
        curriculum = Curriculum(
            curriculumId="CR001",
            majorId="M001",
            curriculumName="Software Engineering",
            academicYear="2026-2027",
        )

        self.assertEqual(curriculum.majorId, "M001")

    def test_curriculum_course_fields_match_data_model(self):
        self.assertEqual(
            [f.name for f in fields(CurriculumCourse)],
            ["curriculumId", "courseId", "courseType"],
        )

    def test_curriculum_course_has_both_key_parts(self):
        item = CurriculumCourse(
            curriculumId="CR001",
            courseId="C001",
            courseType="Compulsory",
        )

        self.assertEqual(
            (item.curriculumId, item.courseId),
            ("CR001", "C001"),
        )

    def test_class_section_fields_match_data_model(self):
        self.assertEqual(
            [f.name for f in fields(ClassSection)],
            [
                "classSectionId",
                "lecturerId",
                "courseId",
                "semesterId",
                "classCode",
                "maxCapacity",
                "currentEnrollment",
                "room",
                "dayOfWeek",
                "startTime",
                "endTime",
            ],
        )

    def test_class_section_can_have_no_assigned_lecturer_yet(self):
        section = ClassSection(
            classSectionId="CS001",
            courseId="C001",
            semesterId="SEM001",
            classCode="SEC01",
            maxCapacity=40,
        )

        self.assertIsNone(section.lecturerId)
        self.assertEqual(section.currentEnrollment, 0)

    def test_class_section_schedule_uses_time_values(self):
        section = ClassSection(
            classSectionId="CS002",
            lecturerId="LT001",
            courseId="C001",
            semesterId="SEM001",
            classCode="SEC02",
            maxCapacity=40,
            currentEnrollment=12,
            room="A101",
            dayOfWeek=2,
            startTime=time(7, 30),
            endTime=time(10, 0),
        )

        self.assertIsInstance(section.startTime, time)
        self.assertIsInstance(section.endTime, time)
        self.assertEqual(section.currentEnrollment, 12)

    def test_assign_lecturer_is_not_implemented_yet(self):
        section = ClassSection(
            classSectionId="CS001",
            courseId="C001",
            semesterId="SEM001",
            classCode="SEC01",
            maxCapacity=40,
        )

        with self.assertRaises(NotImplementedError):
            section.assignLecturer("LT001")

    def test_enrollment_fields_match_data_model(self):
        self.assertEqual(
            [f.name for f in fields(Enrollment)],
            [
                "enrollmentId",
                "studentId",
                "classSectionId",
                "enrollmentDate",
            ],
        )

        item = Enrollment(
            enrollmentId="E001",
            studentId="ST001",
            classSectionId="CS001",
            enrollmentDate=date(2026, 9, 1),
        )

        self.assertIsInstance(item.enrollmentDate, date)

    def test_enrollment_uml_operations_not_implemented_yet(self):
        item = Enrollment(
            enrollmentId="E001",
            studentId="ST001",
            classSectionId="CS001",
            enrollmentDate=date(2026, 9, 1),
        )

        operations = [
            item.registerCourse,
            item.cancelEnrollment,
        ]

        for operation in operations:
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(NotImplementedError):
                    operation()


if __name__ == "__main__":
    unittest.main()
