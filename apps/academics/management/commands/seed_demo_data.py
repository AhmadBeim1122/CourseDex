from django.core.management.base import BaseCommand
from apps.academics.admin import split_outline_to_topics
from apps.academics.models import PastPaper, Program, Semester, Subject, SubTopic, Topic, TopicImage
from apps.academics.models import PastPaper, Program, Semester, Subject, Topic, TopicImage


class Command(BaseCommand):
    help = "Creates a small set of demo Programs/Semesters/Subjects/Topics/PastPapers so you can see the site working."

    def handle(self, *args, **options):
        bsit, _ = Program.objects.update_or_create(
            short_name="BSIT",
            defaults=dict(
                name="BS Information Technology",
                description="A four-year undergraduate program covering programming, networks, databases and web/mobile development.",
                total_semesters=8,
                order=1,
            ),
        )
        bscs, _ = Program.objects.update_or_create(
            short_name="BSCS",
            defaults=dict(
                name="BS Computer Science",
                description="A four-year undergraduate program focused on programming fundamentals, algorithms, systems and theory.",
                total_semesters=8,
                order=2,
            ),
        )

        for program in (bsit, bscs):
            for n in range(1, program.total_semesters + 1):
                Semester.objects.get_or_create(program=program, number=n)

        sem1 = Semester.objects.get(program=bsit, number=1)
        sem2 = Semester.objects.get(program=bsit, number=2)

        prog_fund, _ = Subject.objects.update_or_create(
            semester=sem1,
            slug="programming-fundamentals",
            defaults=dict(
                name="Programming Fundamentals",
                code="IT-101",
                credit_hours="3(3-0)",
                description="Introduction to programming logic, variables, control structures and functions using C/C++.",
                order=1,
            ),
        )
        dld, _ = Subject.objects.update_or_create(
            semester=sem1,
            slug="digital-logic-design",
            defaults=dict(
                name="Digital Logic Design",
                code="IT-102",
                credit_hours="3(2-1)",
                description="Number systems, boolean algebra, logic gates and combinational/sequential circuits.",
                order=2,
            ),
        )
        oop, _ = Subject.objects.update_or_create(
            semester=sem2,
            slug="object-oriented-programming",
            defaults=dict(
                name="Object Oriented Programming",
                code="IT-201",
                credit_hours="3(3-0)",
                description="Classes, objects, inheritance, polymorphism and encapsulation using Java.",
                order=1,
            ),
        )

        topics_data = [
            ("Introduction to Programming", "Programming is the process of writing instructions that a computer can execute. In this topic we cover what a program is, how compilers and interpreters work, and why C/C++ is a good starting language.", "https://www.youtube.com/watch?v=zOjov-2OZ0E"),
            ("Variables and Data Types", "Variables are named storage locations. C/C++ supports data types such as int, float, char, and double. We look at declaration, initialization, and type sizes.", ""),
            ("Operators and Expressions", "Arithmetic, relational, logical and assignment operators, plus operator precedence and associativity, with worked examples.", ""),
            ("Conditional Statements", "if, if-else, and switch statements let a program make decisions. We walk through several examples including nested conditions.", ""),
            ("Loops: for, while, do-while", "Loops let a program repeat instructions. This topic compares for, while and do-while loops and when to use each.", "https://www.youtube.com/watch?v=s9wW2PpJsmQ"),
            ("Functions and Recursion", "Breaking a program into reusable functions, parameter passing, return values, and an introduction to recursion.", ""),
            ("Arrays", "One-dimensional and multi-dimensional arrays, indexing, and common array algorithms like searching and sorting.", ""),
            ("Pointers Basics", "What a pointer is, pointer arithmetic, and the relationship between pointers and arrays.", ""),
        ]
        for i, (title, content, yt) in enumerate(topics_data, start=1):
            Topic.objects.update_or_create(
                subject=prog_fund,
                slug=title.lower().replace(" ", "-").replace(",", "").replace(":", ""),
                defaults=dict(title=title, order=i, content=content, youtube_url=yt),
            )

        # A couple of past papers with different solution types
        PastPaper.objects.update_or_create(
            subject=prog_fund,
            year=2023,
            exam_type=PastPaper.ExamType.FINAL,
            defaults=dict(
                paper_drive_link="https://drive.google.com/file/d/DEMO_PROGFUND_2023_FINAL/view",
                solution_type=PastPaper.SolutionType.TEXT,
                solution_text="Q1) A variable is a named memory location used to store a value that can change during program execution...\n\nQ2) The difference between while and do-while is that do-while executes the loop body at least once...",
            ),
        )
        PastPaper.objects.update_or_create(
            subject=prog_fund,
            year=2022,
            exam_type=PastPaper.ExamType.FINAL,
            defaults=dict(
                paper_drive_link="https://drive.google.com/file/d/DEMO_PROGFUND_2022_FINAL/view",
                solution_type=PastPaper.SolutionType.IMAGE,
                solution_drive_link="https://drive.google.com/drive/folders/DEMO_PROGFUND_2022_SOLUTION",
            ),
        )
        PastPaper.objects.update_or_create(
            subject=prog_fund,
            year=2021,
            exam_type=PastPaper.ExamType.FINAL,
            defaults=dict(
                paper_drive_link="https://drive.google.com/file/d/DEMO_PROGFUND_2021_FINAL/view",
                solution_type=PastPaper.SolutionType.NONE,
            ),
        )

        self.stdout.write(self.style.SUCCESS("Demo data created: 2 programs, subjects, topics and past papers."))
