"""
Object-Oriented Student Management System
-----------------------------------------
Features:
- Create and manage Student objects
- Add, view, search, update, and delete students
- Generate individual and class performance reports
- Save/load student records using JSON
- Validate input and handle invalid operations safely

Run:
    python oop_student_management_system.py

The JSON data file is created automatically beside this script.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class Student:
    """Represents one student and encapsulates student information."""

    PASS_MARK = 40

    def __init__(
        self,
        student_id: str,
        name: str,
        age: int,
        department: str,
        marks: Dict[str, float],
        attendance: float,
        status: str = "Active",
    ):
        self.student_id = self._required_text(student_id, "Student ID").upper()
        self.name = self._required_text(name, "Name")
        self.age = self._validate_age(age)
        self.department = self._required_text(department, "Department")
        self.marks = self._validate_marks(marks)
        self.attendance = self._validate_percentage(attendance, "Attendance")
        self.status = self._required_text(status, "Status")

    @staticmethod
    def _required_text(value, field_name: str) -> str:
        value = str(value).strip()
        if not value:
            raise ValueError(f"{field_name} cannot be empty.")
        return value

    @staticmethod
    def _validate_age(age) -> int:
        try:
            age = int(age)
        except (TypeError, ValueError):
            raise ValueError("Age must be a whole number.") from None
        if not 1 <= age <= 120:
            raise ValueError("Age must be between 1 and 120.")
        return age

    @staticmethod
    def _validate_percentage(value, field_name: str) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a number.") from None
        if not 0 <= value <= 100:
            raise ValueError(f"{field_name} must be between 0 and 100.")
        return value

    @classmethod
    def _validate_marks(cls, marks: Dict[str, float]) -> Dict[str, float]:
        if not isinstance(marks, dict) or not marks:
            raise ValueError("Enter marks for at least one subject.")
        validated = {}
        for subject, mark in marks.items():
            subject = cls._required_text(subject, "Subject")
            validated[subject] = cls._validate_percentage(mark, f"Mark for {subject}")
        return validated

    @property
    def average(self) -> float:
        return sum(self.marks.values()) / len(self.marks)

    @property
    def performance(self) -> str:
        average = self.average
        if average >= 85:
            return "Excellent"
        if average >= 70:
            return "Good"
        if average >= 50:
            return "Average"
        return "Needs Improvement"

    @property
    def result(self) -> str:
        return "PASS" if all(mark >= self.PASS_MARK for mark in self.marks.values()) else "FAIL"

    def update(self, **changes) -> None:
        """Update only supplied fields; validation occurs before values are changed."""
        allowed = {"name", "age", "department", "marks", "attendance", "status"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Unsupported field(s): {', '.join(sorted(unknown))}")

        candidate = {
            "name": self.name,
            "age": self.age,
            "department": self.department,
            "marks": self.marks.copy(),
            "attendance": self.attendance,
            "status": self.status,
        }
        candidate.update(changes)

        # Validate all fields first, so a failed update does not partially modify the student.
        candidate["name"] = self._required_text(candidate["name"], "Name")
        candidate["age"] = self._validate_age(candidate["age"])
        candidate["department"] = self._required_text(candidate["department"], "Department")
        candidate["marks"] = self._validate_marks(candidate["marks"])
        candidate["attendance"] = self._validate_percentage(candidate["attendance"], "Attendance")
        candidate["status"] = self._required_text(candidate["status"], "Status")

        for field, value in candidate.items():
            setattr(self, field, value)

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "age": self.age,
            "department": self.department,
            "marks": self.marks,
            "attendance": self.attendance,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        return cls(**data)


class FileManager:
    """Responsible only for reading and writing student data."""

    def __init__(self, filename: str = "students.json"):
        self.filepath = Path(filename)

    def save(self, students: List[Student]) -> None:
        try:
            data = [student.to_dict() for student in students]
            self.filepath.write_text(json.dumps(data, indent=4), encoding="utf-8")
        except OSError as error:
            raise OSError(f"Could not save data: {error}") from error

    def load(self) -> List[Student]:
        if not self.filepath.exists():
            return []
        try:
            data = json.loads(self.filepath.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("The data file must contain a list of students.")
            students = []
            for index, item in enumerate(data, start=1):
                try:
                    students.append(Student.from_dict(item))
                except (TypeError, ValueError, KeyError) as error:
                    raise ValueError(f"Invalid student record #{index}: {error}") from error
            return students
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not load student data: {error}") from error


class StudentManager:
    """Maintains the collection of students and performs CRUD operations."""

    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.students: Dict[str, Student] = {}

    def add_student(self, student: Student) -> None:
        if student.student_id in self.students:
            raise ValueError(f"Student ID {student.student_id} already exists.")
        self.students[student.student_id] = student

    def get_student(self, student_id: str) -> Student:
        student_id = str(student_id).strip().upper()
        if student_id not in self.students:
            raise KeyError(f"No student found with ID {student_id}.")
        return self.students[student_id]

    def update_student(self, student_id: str, **changes) -> None:
        self.get_student(student_id).update(**changes)

    def delete_student(self, student_id: str) -> Student:
        student = self.get_student(student_id)
        del self.students[student.student_id]
        return student

    def all_students(self) -> List[Student]:
        return sorted(self.students.values(), key=lambda student: student.student_id)

    def save(self) -> None:
        self.file_manager.save(self.all_students())

    def load(self) -> int:
        loaded_students = self.file_manager.load()
        ids = [student.student_id for student in loaded_students]
        if len(ids) != len(set(ids)):
            raise ValueError("The data file contains duplicate student IDs.")
        self.students = {student.student_id: student for student in loaded_students}
        return len(self.students)


class ReportGenerator:
    """Creates readable individual and class performance reports."""

    @staticmethod
    def student_report(student: Student) -> str:
        subjects = ", ".join(
            f"{subject}: {mark:.1f}" for subject, mark in student.marks.items()
        )
        return (
            "\nStudent Report\n"
            "---------------\n"
            f"{student.student_id} | {student.name} | {student.department}\n"
            f"Age: {student.age}\n"
            f"Average: {student.average:.1f}%\n"
            f"Attendance: {student.attendance:.1f}%\n"
            f"Status: {student.status}\n"
            f"Performance: {student.performance}\n"
            f"Result: {student.result}\n"
            f"Subject Marks: {subjects}"
        )

    @classmethod
    def class_report(cls, students: List[Student]) -> str:
        if not students:
            return "No student records available."

        class_average = sum(s.average for s in students) / len(students)
        attendance_average = sum(s.attendance for s in students) / len(students)
        passed = sum(s.result == "PASS" for s in students)
        top_student = max(students, key=lambda s: s.average)

        lines = [
            "\nClass Performance Report",
            "------------------------",
            f"Total students: {len(students)}",
            f"Class average: {class_average:.1f}%",
            f"Average attendance: {attendance_average:.1f}%",
            f"Passed: {passed}",
            f"Failed: {len(students) - passed}",
            f"Top performer: {top_student.name} ({top_student.average:.1f}%)",
            "",
            "ID     | Name                 | Department | Average | Attendance | Result",
            "-" * 78,
        ]
        for student in students:
            lines.append(
                f"{student.student_id:<6} | {student.name:<20} | "
                f"{student.department:<10} | {student.average:>6.1f}% | "
                f"{student.attendance:>9.1f}% | {student.result}"
            )
        return "\n".join(lines)


class StudentManagementApp:
    """Console user interface. Business logic remains in the other classes."""

    def __init__(self):
        self.manager = StudentManager(FileManager())
        self.reports = ReportGenerator()

    @staticmethod
    def read_int(prompt: str) -> int:
        try:
            return int(input(prompt).strip())
        except ValueError:
            raise ValueError("Please enter a valid whole number.") from None

    @staticmethod
    def read_float(prompt: str) -> float:
        try:
            return float(input(prompt).strip())
        except ValueError:
            raise ValueError("Please enter a valid number.") from None

    def input_marks(self, existing: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        marks = {}
        if existing:
            print("Enter subject marks. Type 'done' as the subject name to finish.")
        else:
            print("Enter subject marks. Type 'done' as the subject name to finish.")
        while True:
            subject = input("Subject name (or done): ").strip()
            if subject.lower() == "done":
                break
            if not subject:
                print("Subject name cannot be empty.")
                continue
            if subject in marks:
                print("That subject was already entered.")
                continue
            marks[subject] = self.read_float(f"Mark for {subject} (0-100): ")
        if not marks and existing is None:
            raise ValueError("At least one subject mark is required.")
        return marks if marks else (existing or {})

    def add_student(self) -> None:
        student = Student(
            student_id=input("Student ID: "),
            name=input("Name: "),
            age=self.read_int("Age: "),
            department=input("Department: "),
            marks=self.input_marks(),
            attendance=self.read_float("Attendance (0-100): "),
        )
        self.manager.add_student(student)
        self.manager.save()
        print("Student added successfully.")

    def view_students(self) -> None:
        students = self.manager.all_students()
        if not students:
            print("No student records found.")
            return
        for student in students:
            print(self.reports.student_report(student))

    def search_student(self) -> None:
        student = self.manager.get_student(input("Enter student ID: "))
        print(self.reports.student_report(student))

    def update_student(self) -> None:
        student_id = input("Enter student ID to update: ")
        student = self.manager.get_student(student_id)
        print("Press Enter to keep the current value.")
        changes = {}

        value = input(f"Name [{student.name}]: ").strip()
        if value:
            changes["name"] = value

        value = input(f"Age [{student.age}]: ").strip()
        if value:
            changes["age"] = value

        value = input(f"Department [{student.department}]: ").strip()
        if value:
            changes["department"] = value

        value = input(f"Attendance [{student.attendance}]: ").strip()
        if value:
            changes["attendance"] = value

        value = input(f"Status [{student.status}]: ").strip()
        if value:
            changes["status"] = value

        if input("Update subject marks? (y/n): ").strip().lower() == "y":
            changes["marks"] = self.input_marks(student.marks)

        if not changes:
            print("No changes entered.")
            return
        self.manager.update_student(student_id, **changes)
        self.manager.save()
        print("Student updated successfully.")

    def delete_student(self) -> None:
        student_id = input("Enter student ID to delete: ")
        student = self.manager.get_student(student_id)
        confirm = input(f"Delete {student.name}? (y/n): ").strip().lower()
        if confirm == "y":
            self.manager.delete_student(student_id)
            self.manager.save()
            print("Student deleted.")
        else:
            print("Delete cancelled.")

    def run(self) -> None:
        try:
            count = self.manager.load()
            print(f"Loaded {count} student record(s).")
        except (OSError, ValueError) as error:
            print(f"Warning: {error}")

        actions = {
            "1": self.add_student,
            "2": self.view_students,
            "3": self.search_student,
            "4": self.update_student,
            "5": self.delete_student,
            "6": lambda: print(self.reports.class_report(self.manager.all_students())),
            "7": lambda: (self.manager.save(), print("Data saved successfully.")),
        }

        while True:
            print(
                "\n===== OOP STUDENT MANAGEMENT SYSTEM =====\n"
                "1. Add student\n"
                "2. View all students\n"
                "3. Search student\n"
                "4. Update student\n"
                "5. Delete student\n"
                "6. Generate class performance report\n"
                "7. Save data\n"
                "8. Exit"
            )
            choice = input("Enter your choice (1-8): ").strip()
            if choice == "8":
                try:
                    self.manager.save()
                    print("Data saved. Goodbye!")
                except OSError as error:
                    print(f"Could not save before exit: {error}")
                break
            action = actions.get(choice)
            if action is None:
                print("Invalid choice. Please select a number from 1 to 8.")
                continue
            try:
                action()
            except (ValueError, KeyError, OSError) as error:
                print(f"Operation failed: {error}")
            except (EOFError, KeyboardInterrupt):
                print("\nInput cancelled.")
                break


if __name__ == "__main__":
    try:
        StudentManagementApp().run()
    except KeyboardInterrupt:
        print("\nProgram interrupted.")
