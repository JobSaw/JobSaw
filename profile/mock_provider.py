"""
mock_provider -- Hard-coded mock profile for development and testing.

Implements ProfileProvider with a realistic developer profile containing
a mix of relevant and irrelevant skills so the AI selector agent has
meaningful choices to make.
"""

from profile.models import (
    ProfileCertification,
    ProfileConnection,
    ProfileData,
    ProfileEducation,
    ProfileExperience,
    ProfileSkill,
)
from profile.provider import ProfileProvider


class MockProfileProvider(ProfileProvider):
    """Returns a hard-coded, realistic developer profile.

    The mock profile intentionally includes skills and experience
    that do NOT match typical job postings (e.g. game development,
    embedded systems) alongside mainstream full-stack skills, so
    the AI selector has non-trivial filtering work to do.
    """

    def get_profile(self) -> ProfileData:
        """Return the pre-built mock profile.

        Returns:
            ProfileData with a comprehensive developer profile.
        """
        return ProfileData(
            name="Alex Johnson",
            summary=(
                "Full-stack software engineer with 7 years of experience building "
                "web applications, REST APIs, and cloud-native services. Passionate "
                "about clean architecture, developer tooling, and mentoring junior "
                "engineers. Also dabbles in game development and embedded systems "
                "as personal hobbies."
            ),
            skills=[
                # -- Relevant full-stack skills --
                ProfileSkill(name="Python", proficiency="Advanced", years=6),
                ProfileSkill(name="JavaScript", proficiency="Advanced", years=7),
                ProfileSkill(name="TypeScript", proficiency="Advanced", years=4),
                ProfileSkill(name="React", proficiency="Advanced", years=5),
                ProfileSkill(name="Node.js", proficiency="Advanced", years=5),
                ProfileSkill(name="PostgreSQL", proficiency="Advanced", years=5),
                ProfileSkill(name="MongoDB", proficiency="Intermediate", years=3),
                ProfileSkill(name="Docker", proficiency="Advanced", years=4),
                ProfileSkill(name="Kubernetes", proficiency="Intermediate", years=2),
                ProfileSkill(name="AWS", proficiency="Advanced", years=4),
                ProfileSkill(name="GraphQL", proficiency="Intermediate", years=2),
                ProfileSkill(name="Redis", proficiency="Intermediate", years=3),
                ProfileSkill(name="Git", proficiency="Expert", years=7),
                ProfileSkill(name="CI/CD", proficiency="Advanced", years=4),
                ProfileSkill(name="Django", proficiency="Advanced", years=4),
                ProfileSkill(name="REST API Design", proficiency="Expert", years=6),
                # -- Soft skills --
                ProfileSkill(name="Team Leadership", proficiency="Advanced", years=3),
                ProfileSkill(name="Mentoring", proficiency="Advanced", years=4),
                ProfileSkill(name="Agile / Scrum", proficiency="Advanced", years=5),
                ProfileSkill(name="Technical Writing", proficiency="Intermediate", years=3),
                ProfileSkill(name="Public Speaking", proficiency="Beginner", years=1),
                # -- Less relevant / niche skills --
                ProfileSkill(name="Unity3D", proficiency="Intermediate", years=2),
                ProfileSkill(name="C#", proficiency="Intermediate", years=2),
                ProfileSkill(name="Arduino / Embedded C", proficiency="Beginner", years=1),
                ProfileSkill(name="Blender 3D", proficiency="Beginner", years=1),
                ProfileSkill(name="Rust", proficiency="Beginner", years=1),
                ProfileSkill(name="MATLAB", proficiency="Beginner", years=1),
            ],
            experience=[
                ProfileExperience(
                    title="Senior Software Engineer & Tech Lead",
                    company="CloudScale Inc.",
                    duration="Mar 2022 - Present",
                    description=(
                        "Spearheaded the architectural redesign and core implementation of a multi-tenant SaaS analytics platform serving over "
                        "200 enterprise clients. Led a cross-functional squad of 5 full-stack engineers, driving adoption of Agile methodologies "
                        "and rigorous code review standards. Designed and deployed a robust microservices architecture on AWS (utilizing ECS, "
                        "Lambda, and RDS for scalable data storage). Architected an event-driven data ingestion pipeline using Apache Kafka "
                        "that processes 50,000+ events per second. Reduced end-to-end API latency by 40% globally by implementing strategic "
                        "Redis caching layers and complex SQL query optimization on high-traffic endpoints. Mentored 3 junior developers "
                        "who have since been promoted."
                    ),
                    technologies=[
                        "Python", "TypeScript", "React", "Node.js", "Apache Kafka", "Event-Driven Architecture",
                        "PostgreSQL", "Redis", "AWS (ECS, Lambda, RDS, S3, CloudFront)", "Docker", "Kubernetes",
                        "GraphQL", "GitHub Actions", "Terraform", "Datadog"
                    ],
                ),
                ProfileExperience(
                    title="Full Stack Software Engineer",
                    company="WebForge Studios",
                    duration="Jun 2019 - Feb 2022",
                    description=(
                        "Engineered zero-downtime B2C e-commerce platforms handling 50k+ daily active users and processing $2M+ in monthly "
                        "transactions. Single-handedly integrated complex payment gateways including Stripe, PayPal, and Apple Pay with "
                        "strict adherence to PCI-DSS compliance. Designed a real-time inventory management subsystem using WebSockets to "
                        "prevent race conditions during flash sales. Successfully championed the migration from a monolithic legacy Node.js "
                        "application to a modular microservices architecture, dockerizing the environment and deploying via Jenkins pipelines."
                    ),
                    technologies=[
                        "JavaScript", "TypeScript", "React", "Redux", "Node.js", "Express", "WebSockets",
                        "MongoDB", "PostgreSQL", "Docker", "Jenkins", "Stripe API", "OAuth2", "Jest"
                    ],
                ),
                ProfileExperience(
                    title="Junior Backend Developer",
                    company="StartupHub Analytics",
                    duration="Jan 2018 - May 2019",
                    description=(
                        "Developed mission-critical internal business intelligence tools and dynamic data visualization dashboards "
                        "using Django and React. Built a massive web-scraping infrastructure using Python resulting in a 200% increase "
                        "in aggregate data volume for the ML pipeline. Wrote comprehensive unit and integration test suites, raising "
                        "overall codebase coverage from 45% to 85%. Actively participated in daily standups and bi-weekly sprint planning."
                    ),
                    technologies=[
                        "Python", "Django", "JavaScript", "React", "BeautifulSoup", "Selenium",
                        "PostgreSQL", "Git", "PyTest", "Linux/Bash"
                    ],
                ),
                ProfileExperience(
                    title="Freelance Indie Game Developer",
                    company="Self-Employed",
                    duration="2016 - 2017",
                    description=(
                        "Independently designed, programmed, and published two mobile puzzle games on the Google Play Store, achieving "
                        "a combined total of over 10,000 organic downloads. Implemented custom 2D physics engines and complex UI systems "
                        "using Unity3D and C#. Handled all aspects of the product lifecycle including game design, programming, "
                        "monetization strategy (AdMob integration), and digital marketing campaigns."
                    ),
                    technologies=["Unity3D", "C#", "Blender 3D", "Photoshop", "AdMob", "Google Play Console"],
                ),
            ],
            education=[
                ProfileEducation(
                    degree="M.Sc. Software Engineering",
                    institution="University of Technology",
                    year=2019,
                ),
                ProfileEducation(
                    degree="B.Sc. Computer Science (Graduated with Honors)",
                    institution="University of Technology",
                    year=2017,
                ),
            ],
            certifications=[
                ProfileCertification(
                    name="AWS Certified Solutions Architect - Associate",
                    issuer="Amazon Web Services",
                    year=2023,
                ),
                ProfileCertification(
                    name="Certified Kubernetes Application Developer (CKAD)",
                    issuer="The Linux Foundation",
                    year=2022,
                ),
                ProfileCertification(
                    name="Unity Certified Developer",
                    issuer="Unity Technologies",
                    year=2017,
                ),
            ],
            connections=[
                ProfileConnection(
                    name="Sarah Chen",
                    title="Engineering Manager",
                    company="CloudScale Inc.",
                    relationship="Manager",
                ),
                ProfileConnection(
                    name="David Park",
                    title="Senior DevOps Engineer",
                    company="CloudScale Inc.",
                    relationship="Colleague",
                ),
                ProfileConnection(
                    name="Maria Garcia",
                    title="CTO",
                    company="WebForge Studios",
                    relationship="Former Manager",
                ),
                ProfileConnection(
                    name="James Wilson",
                    title="Lead Game Designer",
                    company="Riot Games",
                    relationship="Industry Contact",
                ),
                ProfileConnection(
                    name="Prof. Elena Kovacs",
                    title="CS Department Head",
                    company="University of Technology",
                    relationship="Academic Mentor",
                ),
            ],
        )
