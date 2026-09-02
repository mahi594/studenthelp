--
-- PostgreSQL database dump
--

\restrict ur4ExtQt8K5HI1oMaaczPTc6MfhEbTbM7UIgu6WHfZuHIHR1BffGTYYZCgBLxx5

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO studenthelp;

--
-- Name: applications; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.applications (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    company_id uuid NOT NULL,
    status character varying NOT NULL,
    applied_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.applications OWNER TO studenthelp;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.audit_logs (
    id uuid NOT NULL,
    institution_id uuid NOT NULL,
    actor_user_id uuid NOT NULL,
    action character varying NOT NULL,
    resource_type character varying NOT NULL,
    resource_id character varying,
    "timestamp" timestamp without time zone,
    metadata_json json
);


ALTER TABLE public.audit_logs OWNER TO studenthelp;

--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.chat_messages (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying NOT NULL,
    content text NOT NULL,
    referenced_company_id uuid,
    created_at timestamp without time zone
);


ALTER TABLE public.chat_messages OWNER TO studenthelp;

--
-- Name: companies; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.companies (
    id uuid NOT NULL,
    name character varying NOT NULL,
    roles character varying[],
    tags character varying[],
    min_cgpa character varying,
    preferred_branches character varying[],
    resume_keywords character varying[],
    apply_url character varying,
    is_curated_verified boolean,
    updated_at timestamp without time zone,
    source_type character varying DEFAULT 'placement_cell'::character varying,
    verified_by character varying,
    verified_at timestamp without time zone,
    confidence character varying DEFAULT 'High'::character varying
);


ALTER TABLE public.companies OWNER TO studenthelp;

--
-- Name: institutions; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.institutions (
    id uuid NOT NULL,
    name character varying NOT NULL,
    domain character varying,
    logo_url character varying,
    primary_color character varying,
    placement_cell_name character varying,
    academic_year character varying,
    created_at timestamp without time zone,
    code character varying
);


ALTER TABLE public.institutions OWNER TO studenthelp;

--
-- Name: interventions; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.interventions (
    id uuid NOT NULL,
    title character varying NOT NULL,
    skill_topic character varying NOT NULL,
    intervention_type character varying,
    target_branch character varying,
    target_student_ids json NOT NULL,
    status character varying,
    pre_avg_score integer,
    post_avg_score integer,
    improvement_delta integer,
    eligible_count integer DEFAULT 0 NOT NULL,
    pre_assessed_count integer DEFAULT 0 NOT NULL,
    reassessed_count integer DEFAULT 0 NOT NULL,
    institution_id uuid,
    created_by_user_id uuid NOT NULL,
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);


ALTER TABLE public.interventions OWNER TO studenthelp;

--
-- Name: job_listings; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.job_listings (
    id uuid NOT NULL,
    source character varying,
    external_id character varying NOT NULL,
    company_name character varying NOT NULL,
    role_title character varying NOT NULL,
    location character varying,
    description_snippet text,
    apply_url character varying NOT NULL,
    posted_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL,
    fetched_at timestamp without time zone
);


ALTER TABLE public.job_listings OWNER TO studenthelp;

--
-- Name: learning_resources; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.learning_resources (
    id uuid NOT NULL,
    subject character varying NOT NULL,
    topic character varying NOT NULL,
    title character varying NOT NULL,
    url character varying NOT NULL,
    resource_type character varying,
    rank integer
);


ALTER TABLE public.learning_resources OWNER TO studenthelp;

--
-- Name: leetcode_logs; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.leetcode_logs (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    problem_title character varying NOT NULL,
    problem_slug character varying,
    difficulty character varying NOT NULL,
    topic character varying,
    notes text,
    solved_at timestamp without time zone
);


ALTER TABLE public.leetcode_logs OWNER TO studenthelp;

--
-- Name: mock_interview_sessions; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.mock_interview_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    company_id uuid,
    role_or_subject character varying NOT NULL,
    transcript json NOT NULL,
    status character varying NOT NULL,
    overall_score integer,
    feedback json,
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);


ALTER TABLE public.mock_interview_sessions OWNER TO studenthelp;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.notifications (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    type character varying NOT NULL,
    title character varying NOT NULL,
    body text,
    link character varying,
    is_read boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.notifications OWNER TO studenthelp;

--
-- Name: prep_plans; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.prep_plans (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    target_company_id uuid,
    days_total integer NOT NULL,
    tasks json NOT NULL,
    progress_percent integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.prep_plans OWNER TO studenthelp;

--
-- Name: qa_answers; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.qa_answers (
    id uuid NOT NULL,
    question_id uuid NOT NULL,
    author_id uuid NOT NULL,
    body text NOT NULL,
    upvotes integer NOT NULL,
    is_hidden boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.qa_answers OWNER TO studenthelp;

--
-- Name: qa_questions; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.qa_questions (
    id uuid NOT NULL,
    author_id uuid NOT NULL,
    company_id uuid,
    title character varying NOT NULL,
    body text NOT NULL,
    tags character varying[],
    is_hidden boolean NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.qa_questions OWNER TO studenthelp;

--
-- Name: qa_upvotes; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.qa_upvotes (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    answer_id uuid NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.qa_upvotes OWNER TO studenthelp;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.questions (
    id uuid NOT NULL,
    round_id uuid,
    subject character varying NOT NULL,
    difficulty character varying,
    tags character varying[],
    text text NOT NULL,
    answer_or_hint text,
    source character varying,
    submitted_by character varying
);


ALTER TABLE public.questions OWNER TO studenthelp;

--
-- Name: quiz_questions; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.quiz_questions (
    id uuid NOT NULL,
    company_id uuid,
    subject character varying NOT NULL,
    difficulty character varying,
    question_text text NOT NULL,
    options json NOT NULL,
    correct_option_index integer NOT NULL,
    explanation text,
    status character varying NOT NULL,
    generated_by character varying,
    reviewed_by_user_id uuid,
    reviewed_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.quiz_questions OWNER TO studenthelp;

--
-- Name: quiz_results; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.quiz_results (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    subject character varying NOT NULL,
    score_percent integer NOT NULL,
    taken_at timestamp without time zone
);


ALTER TABLE public.quiz_results OWNER TO studenthelp;

--
-- Name: readiness_scores; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.readiness_scores (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    composite_score integer,
    breakdown json NOT NULL,
    computed_at timestamp without time zone,
    data_status character varying DEFAULT 'sufficient'::character varying NOT NULL,
    algorithm_version character varying DEFAULT 'v1'::character varying
);


ALTER TABLE public.readiness_scores OWNER TO studenthelp;

--
-- Name: resumes; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.resumes (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    file_url character varying NOT NULL,
    storage_key character varying,
    parsed_text text,
    parsed_json json,
    target_company_id uuid,
    match_result json,
    created_at timestamp without time zone
);


ALTER TABLE public.resumes OWNER TO studenthelp;

--
-- Name: roadmaps; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.roadmaps (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    horizon_months integer NOT NULL,
    phases json NOT NULL,
    based_on_quiz_snapshot json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    target_company_ids json,
    target_company_names json
);


ALTER TABLE public.roadmaps OWNER TO studenthelp;

--
-- Name: rounds; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.rounds (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    order_index integer NOT NULL,
    round_type character varying NOT NULL,
    subjects_tested character varying[],
    difficulty character varying,
    notes text
);


ALTER TABLE public.rounds OWNER TO studenthelp;

--
-- Name: users; Type: TABLE; Schema: public; Owner: studenthelp
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    name character varying NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    branch character varying,
    grad_year integer,
    cgpa character varying,
    role character varying NOT NULL,
    college_name character varying,
    target_company_ids uuid[],
    created_at timestamp without time zone,
    email_verified boolean DEFAULT false NOT NULL,
    leetcode_username character varying,
    leetcode_daily_goal integer DEFAULT 1 NOT NULL,
    leetcode_total_solved integer DEFAULT 0 NOT NULL,
    leetcode_easy_solved integer DEFAULT 0 NOT NULL,
    leetcode_medium_solved integer DEFAULT 0 NOT NULL,
    leetcode_hard_solved integer DEFAULT 0 NOT NULL,
    leetcode_streak integer DEFAULT 0 NOT NULL,
    leetcode_last_solved_date character varying,
    must_change_password boolean NOT NULL,
    institution_id uuid
);


ALTER TABLE public.users OWNER TO studenthelp;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.alembic_version (version_num) FROM stdin;
a1b2c3d4e5f6
\.


--
-- Data for Name: applications; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.applications (id, user_id, company_id, status, applied_at, updated_at) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.audit_logs (id, institution_id, actor_user_id, action, resource_type, resource_id, "timestamp", metadata_json) FROM stdin;
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.chat_messages (id, user_id, role, content, referenced_company_id, created_at) FROM stdin;
09f27dc1-709d-4e3f-8423-a37f47d8910f	10f2dfe7-169e-4b07-acdb-4547e13781d5	user	tell as i am new student	9494f712-46cc-4037-ad76-5510fb43332d	2026-08-21 11:08:47.329987
a52ed603-c618-43cd-b467-0c21e66637ec	10f2dfe7-169e-4b07-acdb-4547e13781d5	assistant	Welcome to your placement preparation journey! Since you're just starting out, here is a quick breakdown of what the hiring process looks like for top companies like **Microsoft**, based on our verified data:\n\n### Microsoft Hiring Process:\n1. **Online Assessment (OA):** \n   * **Difficulty:** Medium\n   * **What's tested:** 1 coding question (DSA) + MCQs on CS fundamentals (like DBMS, OS, OOP) and aptitude.\n2. **Technical Rounds:** \n   * **Difficulty:** Medium to Hard\n   * **What's tested:** Strong Data Structures & Algorithms (DSA), Object-Oriented Programming (OOP), Database Management Systems (DBMS), and System Design. Microsoft interviewers heavily emphasize writing clean code and handling edge cases, not just getting the right answer.\n3. **HR / Behavioral Round:** \n   * **Difficulty:** Easy\n   * **What's tested:** Your background, teamwork, and cultural fit.\n\n---\n\n### Your Next Steps as a New Student:\n* **Master the Basics:** Start with one programming language (C++, Java, or Python) and focus heavily on **DSA** (Arrays, Strings, Linked Lists, Trees, Graphs).\n* **Core CS Subjects:** Don't skip **DBMS, Operating Systems (OS), and OOP**—they are crucial for both OAs and technical interviews.\n* **Aptitude & Practice:** Regularly practice logical reasoning and quantitative aptitude.\n\nFeel free to ask if you need help planning your study schedule or building your resume!	9494f712-46cc-4037-ad76-5510fb43332d	2026-08-21 11:08:47.33001
\.


--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.companies (id, name, roles, tags, min_cgpa, preferred_branches, resume_keywords, apply_url, is_curated_verified, updated_at, source_type, verified_by, verified_at, confidence) FROM stdin;
8a20ae28-8072-4b33-9ec3-7e4fa2cdb5dc	Google	{SDE-1,APM}	{product-based,faang}	8.0	{CSE,IT,ECE}	{DSA,"System Design",Python,Java}	https://careers.google.com/students/	t	2026-08-21 08:13:58.734612	placement_cell	\N	\N	High
9494f712-46cc-4037-ad76-5510fb43332d	Microsoft	{SDE-1}	{product-based,faang-adjacent}	7.5	{CSE,IT,ECE}	{DSA,OOP,C#,Azure}	https://careers.microsoft.com/students/	t	2026-08-21 08:13:58.753924	placement_cell	\N	\N	High
296ba61e-8a64-474e-9051-ba5cbdd1fda8	Amazon	{SDE-1}	{product-based,faang}	7.0	{CSE,IT,ECE,EEE}	{DSA,"Leadership Principles",AWS}	https://www.amazon.jobs/en/teams/university	t	2026-08-21 08:13:58.762218	placement_cell	\N	\N	High
b4914043-13d9-43e4-9833-cc9dbcb4e2c5	TCS	{Ninja,Digital}	{service-based,mass-recruiter}	6.0	{CSE,IT,ECE,EEE,MECH,CIVIL}	{Aptitude,Communication}	https://www.tcs.com/careers	t	2026-08-21 08:13:58.769498	placement_cell	\N	\N	High
1fca9c60-2faf-459b-a5c6-a7f5831b9024	Infosys	{SP,"Digital Specialist Engineer"}	{service-based,mass-recruiter}	6.5	{CSE,IT,ECE,EEE,MECH}	{Aptitude,Communication}	https://www.infosys.com/careers/	t	2026-08-21 08:13:58.776458	placement_cell	\N	\N	High
b3b086e1-364f-464e-9dee-b60d5f179843	Razorpay	{SDE-1}	{product-based,fintech,startup}	7.5	{CSE,IT}	{DSA,"System Design",Node.js,Go}	https://razorpay.com/jobs/	t	2026-08-21 08:13:58.783444	placement_cell	\N	\N	High
\.


--
-- Data for Name: institutions; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.institutions (id, name, domain, logo_url, primary_color, placement_cell_name, academic_year, created_at, code) FROM stdin;
\.


--
-- Data for Name: interventions; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.interventions (id, title, skill_topic, intervention_type, target_branch, target_student_ids, status, pre_avg_score, post_avg_score, improvement_delta, eligible_count, pre_assessed_count, reassessed_count, institution_id, created_by_user_id, created_at, completed_at) FROM stdin;
\.


--
-- Data for Name: job_listings; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.job_listings (id, source, external_id, company_name, role_title, location, description_snippet, apply_url, posted_at, expires_at, fetched_at) FROM stdin;
09f5f908-4e2a-4484-a3c8-874367a140fc	adzuna	5864443117	Koffeetech Communications	Web Developer	Mumbai, Maharashtra	Job brief We are looking for an outstanding Web Developer to be responsible for the coding, innovative design and layout of our website. Web developer responsibilities include building website from concept all the way to completion from the bottom up, fashioning everything from the home page to site layout and function. Responsibilities • Write well designed, testable, efficient code by using best software development practices • Create website layout/user interface by using standard HTML/CSS p…	https://www.adzuna.in/land/ad/5864443117?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=86D41B0FB2FAEDB72058771F6197865ADF1FE80E	2026-09-01 16:23:19	2026-10-01 11:15:19.481641	2026-09-01 11:15:19.561665
703a5016-6e7a-4fd3-a819-a1af65c18a1b	adzuna	5864432263	INSIDEA	Web Developer	Mumbai, Maharashtra	About the company: At INSIDEA, we are a fully remote organisation, hiring top talents from across the globe to deliver exceptional digital marketing and HubSpot solutions. Our diverse services are designed to enhance your brand’s online presence and drive real, measurable growth. From marketing optimization and content creation to full-scale HubSpot integration, we provide a holistic approach to transform your digital experience and maximize performance. We are proud to be a Top 10 Elite HubSpo…	https://www.adzuna.in/land/ad/5864432263?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=A19AC9059ACDA9F8D53F8DDE586498A33751A9DE	2026-09-01 16:21:52	2026-10-01 11:15:19.492375	2026-09-01 11:15:19.561679
fb7b5ab5-bd61-4dc1-a9b5-402f2ad0d542	adzuna	5864426896	Artech L.L.C.	Web Developer	Mumbai, Maharashtra	Web Developer Job Duties: Regular exposure to business stakeholders and executive management, as well as the authority and scope to apply your expertise to many interesting technical problems. Strong understanding of OOPS concept, Javascript, Python & Node JS Candidate must have a strong understanding of UI, cross-browser compatibility, general web functions and standards. The position requires constant communication with colleagues. Experience in planning and delivering software platforms used…	https://www.adzuna.in/land/ad/5864426896?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=A05FD6092232E0786F59B62CC594346814551D1D	2026-09-01 16:20:53	2026-10-01 11:15:19.49336	2026-09-01 11:15:19.561687
c1401a09-8aeb-4610-892f-45e03fec9bce	adzuna	5864426800	Allegion India	Web Developer	Bangalore, Karnataka	Web Developer – Global Web Team About Allegion : At Allegion, we help keep people safe and secure where they live, work, and visit. With more than 25 brands sold in nearly 130 countries worldwide, we specialize in security solutions around the doorway and beyond — including residential and commercial locks, door closers and exit devices, steel doors and frames, and advanced access control and workforce productivity systems. About the role : We are seeking an AI-first Front-End / CMS Developer w…	https://www.adzuna.in/land/ad/5864426800?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=2A0C2F8650D96008E7522540272098E7ED967E0D	2026-09-01 16:20:52	2026-10-01 11:15:19.494222	2026-09-01 11:15:19.561698
f3d6ff21-2e7e-47fe-b02a-a3c748983fe6	adzuna	5864433726	Jase HR Solutions	Web Developer	Bangalore, Karnataka	What Your Impact Will Look Like Work with a CMS Lead Developer to complete client contracts and projects Work with CMS Project Manager to receive appropriate application data from clients Set up all applications within the CMS tool for each project Create CMS admin tools and widgets as required for project Test all completed work to ensure proper and error free functionality Complete all programming tasks while following company code standards Complete and respond to all change requests from cl…	https://www.adzuna.in/land/ad/5864433726?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=C35F078A0C01D0133FD74808D45B0307B1E3046E	2026-09-01 16:22:05	2026-10-01 11:15:19.494869	2026-09-01 11:15:19.561706
3983aa81-2b1d-4118-bd34-435bda50fe86	adzuna	5864432423	Identy.io	Frontend Web Developer	Bangalore, Karnataka	Company Description Identy.io is a leader in mobile biometric authentication, delivering secure and user-friendly identity verification solutions to government and corporate customers. Our technology enables use cases such as border control and remote financial onboarding by leveraging face and fingerprint recognition to reduce fraud and improve user experience. All biometric data is processed directly on the device, enhancing privacy, reliability, and scalability without the need for additiona…	https://www.adzuna.in/land/ad/5864432423?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=17DC1E69CE89E5F3F59B1D0DB36712E032361E01	2026-09-01 16:21:54	2026-10-01 11:15:19.495455	2026-09-01 11:15:19.561712
ff91f675-8fc8-401e-9bb3-96413007917c	adzuna	5864440931	Indian School of Business	Manager - Web Developer	Hyderabad, Telangana	 We're Hiring: Manager - Web Developer | Marketing & Communications  Hyderabad (On-site) | Full-time Are you a hands-on web developer who loves owning projects end-to-end — from CMS content to code deployment? Join our Marcom team and take charge of our website's technical backbone!  About the Role We're looking for a detail-oriented Web Developer to manage our website's technical and content operations — from authoring in Umbraco CMS to building front-end components, implementing SEO, developi…	https://www.adzuna.in/land/ad/5864440931?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=A38DE7B006D4B41F2A19F596BA34458A6E7B81C3	2026-09-01 16:23:06	2026-10-01 11:15:19.49737	2026-09-01 11:15:19.561718
7fb8a73e-b484-4aa5-a765-137a2cb4d50f	adzuna	5864426590	Emcure Pharmaceuticals Limited	Web Development Specialist	India	Designation: Web Development and Maintenance – Assistant Manager/Manager Experience: 4-7 years of experience managing enterprise websites. Proven experience handling websites independently from development through deployment and maintenance. Experience with large corporate with the multiple subsidiaries/microsites Description: The candidate will be responsible for the end-to-end management of the company's web presence, including website development, maintenance, security, performance managemen…	https://www.adzuna.in/land/ad/5864426590?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=BBFE84953B99F7050394762EBF0759F28C9CED77	2026-09-01 16:20:51	2026-10-01 11:15:19.498878	2026-09-01 11:15:19.561725
478c83aa-bbdd-49c1-8b6d-78e6aeed0db6	adzuna	5864431003	Tata Consultancy Services	Java Web Developer	Bangalore, Karnataka	Greetings from TCS JD : Position: Java Developer Job Location: Bangalore Experience: 6-8 years Role & responsibilities: Must Have: Position: Java Developer Required Skill Sets: Java, Microservices, Springboot, Python 6 years of exp Strong Java backend Engineer Java Springboot Micro services Rest API’s Python – AI Models creation, Fine Tuning Models, AI and GEN AI experience Location – BLR only Working experience on Agile projects Flexible with the time	https://www.adzuna.in/land/ad/5864431003?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=CF7A0FDB7ABCDEA0219E57193758D7B29AAECDBD	2026-09-01 16:21:43	2026-10-01 11:15:19.501295	2026-09-01 11:15:19.561731
fb0fd14d-ddc2-4eca-af02-97adf2165769	adzuna	5864442781	MVI Technologies	Web Developer – Java Technologies	Chennai, Tamil Nadu	Web Developer – Java Technologies for FinTech Domain (Chennai) Job description We are looking for a Web Developer – Java Technologies who is willing to work in emerging technologies in the FinTech sector (payment processing). Responsibilities Design, develop and maintain new and existing software modules for our banking and payment service provider customers worldwide Write testable and efficient code Develop reusable code that are optimized for high performance, robustness and scalability for …	https://www.adzuna.in/land/ad/5864442781?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=E2483625BB18DEA6565D89EBFB07AD7AE583E145	2026-09-01 16:23:16	2026-10-01 11:15:19.503533	2026-09-01 11:15:19.561737
cae1ba64-20ea-4704-bfd8-3093e3266f1e	adzuna	5864426187	RBC Worldwide	Web Designer & Developer	Hyderabad, Telangana	Code meets creativity! RBC Worldwide is on the lookout for a versatile Web Design and Developer who bridges the gap between stunning visuals and seamless functionality. We need a professional with strong expertise in both web design and web development someone who can craft an exceptional user experience and write the clean code to bring it to life from scratch. Key Details:  Location: Particularly looking only from Hyderabad - Full time  Experience: 5 Years & More  Mandatory: Prior experience …	https://www.adzuna.in/land/ad/5864426187?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=09B6FE79D1199170FB2A70BAEEC92ECD7BC2468C	2026-09-01 16:20:44	2026-10-01 11:15:19.507061	2026-09-01 11:15:19.561743
cdf01de6-190e-466f-9d93-00714d8d18dd	adzuna	5864437653	Revive Global Ventures	Brand Identity • Web Development • Social Media • Performance Marketing	India	 We're Building a Curated Network of Elite Freelancers — And We Want the Best in the Room Brand Identity • Web Development • Social Media • Performance Marketing At REVIVE Global Ventures , we don't chase talent — we curate it. We're expanding our delivery partner network and inviting a select group of experienced freelancers to join us for upcoming international projects . If you've built work you're proud of for startups and technology companies — whether in India or across the globe — this i…	https://www.adzuna.in/land/ad/5864437653?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=30096F000FC7EE09A1C95585B7C3058A98D9EFCA	2026-09-01 16:22:40	2026-10-01 11:15:19.508403	2026-09-01 11:15:19.561749
bfe98ae9-d6a8-4043-85d6-f70633b731eb	adzuna	5864425643	DIGI - MAA	Shopify Developer	Ahmedabad, Gujarat	Job Title: Web/Shopify Developer Location: Ahmedabad (On-site) Job Type: Full-time Experience: 1–3 Years About the Role We are looking for a talented and detail-oriented Web Developer to join our team. The ideal candidate should have strong front-end development skills, hands-on experience with Shopify, and the ability to build responsive, high-quality websites. Experience with WordPress will be considered an added advantage. Key Skills Shopify Store Design & Theme Customization HTML5 CSS3 Java…	https://www.adzuna.in/land/ad/5864425643?se=_prLaval8RGGYI73n1NTOA&utm_medium=api&utm_source=7c761630&v=8E49C4748D94350BF099E21A29A97053CF803FE0	2026-09-01 16:20:36	2026-10-01 11:15:19.509646	2026-09-01 11:15:19.561756
fda76a90-bc9a-4c0d-a795-95bf23b002b7	adzuna	4686706438	Unknown	Web Developer	Delhi, India	Web Developer is responsible for the coding, design and layout of a website according to a company's specifications. As the role takes into consideration user experience and function, a certain level of both Looking for Senior Web developer (Freelancer) with 5yrs of experience for Dwarka Sector 12, Delhi. Pls contact with updated cv and portfolio at jobsrjcube.com	https://www.adzuna.in/details/4686706438?utm_medium=api&utm_source=7c761630	2024-05-10 07:39:01	2026-10-01 11:15:19.510351	2026-09-01 11:15:19.561762
a91a406a-a67d-4437-9925-cd5f62b00107	adzuna	4686701678	Unknown	Web Developer	Ernakulam, Kerala	Job Description International IT company in Cochin looking for Web developer PHP/java. Direct walk-in & Direct Joining Process ( careercochigmail.com, infoonei-s.com ) Job Vacancy: - web developer Senior web developers Senior Web developer cum Project Lead Job Location:- Kochi, Kakkanadu Salary: As per the industry standards JobDescription: - As a Backend Developer, you will work as a part/Leader of a software development team and be responsible for designing, implementing, and maintaining the …	https://www.adzuna.in/details/4686701678?utm_medium=api&utm_source=7c761630	2024-05-10 07:38:27	2026-10-01 11:15:19.511625	2026-09-01 11:15:19.561768
1927586a-cd93-4148-9966-f3d1084cd637	adzuna	5854074780	fx retina	Web Developer	Lucknow, Uttar Pradesh	Job Description: Job Title: Web Developer (full stack developer having exiperince in WordPress & Shopify as well) Company: Fx Retina Digital Marketing Agency Location: Lucknow, Indira Nagar Job Type: Full-time: In-office only Salary: Based on skills and experience Experience Required: Minimum 2 years About Fx Retina Fx Retina is a performance-driven digital marketing agency focused on scaling businesses through paid advertising on Google and Meta platforms. Our team thrives on data, creativity,…	https://www.adzuna.in/details/5854074780?utm_medium=api&utm_source=7c761630	2026-08-24 07:14:43	2026-10-01 11:15:19.512477	2026-09-01 11:15:19.561774
8e2780dc-5ae9-4b2e-863f-6691540ed2d1	adzuna	4686706187	Unknown	Web Developer	Kolhapur, Maharashtra	Job descriptionJob description of Web Developer-Well designed, testable, efficient code by using best software development practices.Create website layout/user interface by using standard HTML/CSS practices.Integrate data from various back-end services and databases.Gather and refine specifications and requirements based on technical needs.Top-notch programming skills and in-depth knowledge of modern HTML/CSS.creating website designs.producing sample sites.keeping up to date with recent technol…	https://www.adzuna.in/details/4686706187?utm_medium=api&utm_source=7c761630	2024-05-10 07:38:59	2026-10-01 11:15:19.513953	2026-09-01 11:15:19.561781
be8629b2-fa69-4520-8969-6e0d831e3bd2	adzuna	5855696371	Thoughtlogik Technology Solutions Pvt Ltd	Web Developer	Coimbatore North, Coimbatore	We are seeking a talented Web Developer & Designer with 1 to 5 years of experience to join our team. The ideal candidate will be responsible for designing, coding, and improving our web-based applications and websites to meet both functional and aesthetic goals. You will work closely with cross-functional teams to bring concepts to life and ensure a seamless user experience. Creativity, attention to detail, and a strong command of web technologies are essential. Key Responsibilities Design visu…	https://www.adzuna.in/details/5855696371?utm_medium=api&utm_source=7c761630	2026-08-26 01:05:40	2026-10-01 11:15:19.514674	2026-09-01 11:15:19.561787
a447b60e-57ec-4a93-98a9-05d874a071e5	adzuna	4686700180	Unknown	Web Developer	Alwar, Rajasthan	About Company:- We “Webbyte Technologies Pvt. Ltd.” dedicated to developing a truly innovative and superior service to help consumers make better buying decisions, and currently among the top 2000 websites in India. Each month we help millions of consumers to find and purchase the best discounted products from our vast catalogue of merchant products. We receive well over a half million visitors every month to our website so any change you make is going to impact millions within a short span. In…	https://www.adzuna.in/details/4686700180?utm_medium=api&utm_source=7c761630	2024-05-10 07:38:16	2026-10-01 11:15:19.515408	2026-09-01 11:15:19.561793
454a2911-beed-4c7e-a2cd-3f8e35ecf127	adzuna	5718934333	Gururo	Web Developer	Bangalore, Karnataka	Job Title: Web Developer (WordPress) – Remote / Internship Available Company: Gururo Department: Technology / Web Development Location: Remote Job Type: Full-Time / Part-Time / Internship Experience Required: 1 year experience in WordPress development OR Freshers can apply for internship (training  learning opportunity) Role Overview Gururo is looking for a Web Developer with WordPress experience. We are also open to interns who are eager to learn WordPress development and gain hands-on experie…	https://www.adzuna.in/details/5718934333?utm_medium=api&utm_source=7c761630	2026-05-05 05:53:36	2026-10-01 11:15:19.516064	2026-09-01 11:15:19.5618
9144c270-ef09-4e88-85f3-a30d4f323494	adzuna	3297100677	HuntingCube	SDE-2,3/Lead/EM/Staff engineer	Delhi, India	Responsibilities: Lead the development of the back-end systems for our first product. Build reliable, secure and performant back-end systems. Drive test coverage and continuous delivery automation within the team. Mentor and provide feedback to teammates. Requirements : 3 years of software development experience. Strong computer science fundamentals. Deep and wide knowledge of Java ecosystem. Can write code that is readable, maintainable, secure and performant. Know the importance of tests and …	https://www.adzuna.in/details/3297100677?utm_medium=api&utm_source=7c761630	2022-07-07 06:39:04	2026-10-02 06:08:19.722878	2026-09-02 06:08:19.731035
abb2ef2b-d4b3-4b0c-a094-7bfac8fe63e8	adzuna	5864442054	Bullet Microdrama OTT	Back End Developer	New Delhi, Delhi	Senior Full Stack Developer (Typescript / Node.js / Express.js / NestJS / React / GCP / Postgresql) Experience: 8 years Band - SDE 3 Location: Noida, Uttar Pradesh, India — full-time on-site (no hybrid, no remote) Department: Engineering — Platform & Product Reports to: Engineering Manager / Principal Engineer About the Role We are looking for a Senior Full Stack Developer to design, build, and scale distributed backend services and modern web applications. You will own end-to-end delivery — fr…	https://www.adzuna.in/land/ad/5864442054?se=svGesZSm8RGUNa3mkcr13g&utm_medium=api&utm_source=7c761630&v=BE871E37D7E995FF497AB8BDAC93B496AC68DEE9	2026-09-01 16:23:12	2026-10-02 06:08:19.715566	2026-09-02 06:08:19.730999
e55338a6-65d4-4001-ae9d-3a3cd172dd27	adzuna	4514376195	Qrata	SDE	Delhi, India	About Us We began in 2015 with an entrepreneurial vision to bring a digital change in the manufacturing landscape of India. With a team of 1500(1k cluster guys) we are working towards the digital transformation of business in the manufacturing industry across domains like Footwear, Apparel, Textile, Accessories etc. We are backed by investors such as Info Edge (Naukri.com ), Matrix Partners, Sequoia, Water Bridge Ventures and select Industry leaders. Today, we have enabled 4000 Manufacturers to…	https://www.adzuna.in/details/4514376195?utm_medium=api&utm_source=7c761630	2024-01-07 15:07:50	2026-10-02 06:08:19.71703	2026-09-02 06:08:19.731005
d84709e7-c46e-4ce2-bc00-69661d695644	adzuna	5807483786	LT-Larsen & Toubro	SDE	Delhi, India	Job Description: Senior Electrical Design Engineer Job Purpose:- We are seeking an experienced Senior Electrical Design Engineer to lead the development, design, and engineering of complex electrical systems. The ideal candidate will possess deep technical expertise in power distribution system and interfaces. Qualifications:- B.Tech / B.E. in Electrical Engineering (Essential) M.Tech / M.E. in Electrical Engineering (Desirable) Experience Industry: Marine, Aeronautical, or Power Generation & D…	https://www.adzuna.in/details/5807483786?utm_medium=api&utm_source=7c761630	2026-07-20 03:14:57	2026-10-02 06:08:19.717687	2026-09-02 06:08:19.731009
163ca1af-463a-4e7a-b192-84e171efcd42	adzuna	4514376171	Qrata	SDE (Python)	Delhi, India	Roles & Responsibilities • Writing and testing code, debugging programs and integrating applications with third-party web services. To be successful in this role, you should have experience using server-side logic and work well in a team. • Ultimately, you'll build highly responsive web applications that align with our business needs. • Write effective, scalable code Develop back-end components to improve responsiveness and overall performance Integrate user-facing elements into applications. •…	https://www.adzuna.in/details/4514376171?utm_medium=api&utm_source=7c761630	2024-01-07 15:07:48	2026-10-02 06:08:19.718263	2026-09-02 06:08:19.731013
13066fd7-026f-412f-b1ac-42eb50ed7345	adzuna	2795055684	Qrata	SDE-3 (Python)	Delhi, India	About the company: Clinical Trials are the biggest bottleneck in bringing new drugs, devices, and vaccines to patients. On average, getting a new drug through the trial process takes nearly a decade and frequently costs $1B. To make it worse, the process is inflicted with a great number of transparency issues. We are aiming to solve this through technology and platformization of clinical trials. We develop and offer next-generation technology platforms to pharmaceutical and biotech companies fo…	https://www.adzuna.in/details/2795055684?utm_medium=api&utm_source=7c761630	2022-01-07 04:36:11	2026-10-02 06:08:19.718734	2026-09-02 06:08:19.731016
f03b4117-6362-478e-881d-825396449c5a	adzuna	2814879333	StockPe	SDE (React Native)	Delhi, India	Are you a React Native Developer? This is not a usual job description where after reading the roles and responsibilities you are still unclear about the work you’ll be doing and how your contributions will impact the customers. Here, we’ll tell you exactly what you’re getting into and you decide for yourself if we’re worthy of your application. Deal? Let’s do it! About Us: StockPe is gamifying financial education for young Indians thereby making them financially educated. We are a small team of…	https://www.adzuna.in/details/2814879333?utm_medium=api&utm_source=7c761630	2022-01-15 04:26:33	2026-10-02 06:08:19.719222	2026-09-02 06:08:19.731018
28015d38-6299-4e8c-ab5f-039745e368a0	adzuna	5623893665	Timble Technologies	L3 SDE(Python-Django)	Delhi, India	Job Title: L3 SDE (Python- Django) Location: Arjan Garh, MG Road (Delhi) Job Type: Full-time, On site Pay Range: RS. 30,000- 70,000 IMMEDIATE JOINERS REQUIRED About Us: Our Aim is to develop ‘More Data, More Opportunities’. We take pride in building a cutting-edge AI solutions to help financial institutions mitigate risk and generate comprehensive data. Elevate Your Business's Credibility with Timble Glance's Verification and Authentication Solutions. Responsibilities • Writing and testing code…	https://www.adzuna.in/details/5623893665?utm_medium=api&utm_source=7c761630	2026-02-11 11:44:46	2026-10-02 06:08:19.720167	2026-09-02 06:08:19.731021
8a1486f0-24f3-4d97-b7b0-51d4253525ac	adzuna	1894228438	O4S	Software Engineer-SDE III	Delhi, India	We are looking for a backend developer to join our team who shares our passion for making the lives of API developers and consumers easier. If you love thinking big and delving deep and enjoy envisioning truly elegant solutions, this role is definitely for you. What you will be Doing - You will abstract away complex data interactions with easy-to-use APIs that will power several mobile and web applications. - You will also own, scale, and maintain the computational and storage infrastructure fo…	https://www.adzuna.in/details/1894228438?utm_medium=api&utm_source=7c761630	2020-12-22 03:34:45	2026-10-02 06:08:19.720919	2026-09-02 06:08:19.731024
36e0c3b5-e68c-4a76-8ed5-02c0b5c39254	adzuna	2239678846	Zyoin Web Private Limited	Backend Engineer- SDE 2	Delhi, India	About OneAssist OneAssist is founded with a vision to provide a ubiquitous platform for assistance & protection services to customers. A leader in Assistance and Protection products across Home Appliances, Personal Electronics, Physical and Mobile Wallets, OneAssist is a Technology-led organization. It has created a horizontal Assitance and Protection platform powered by Technology, Analytics and Data Science. OneAssist wants to provide consumers the convenience of availing assistance and prote…	https://www.adzuna.in/details/2239678846?utm_medium=api&utm_source=7c761630	2021-06-09 13:17:17	2026-10-02 06:08:19.721423	2026-09-02 06:08:19.731026
4fcd31a6-efce-4596-8f52-8e5858f21bac	adzuna	5697249696	Amazon	SDE II , Stores TA	Delhi, India	Description This role is for the AFT Inbound Foundations and Routing team (IBFR) team which is responsible to build core software components/services that orchestrate the movement of inventory within a warehouse and interfacing with sortation and SCOT systems for high fidelity promise and planning decisions. Worldwide, the IBFR team supports 570 FCs across NA, EU and JP regions. With rapid expansion into new geographies, innovations in supply chain, delivery models and customer experience, incr…	https://www.adzuna.in/details/5697249696?utm_medium=api&utm_source=7c761630	2026-04-12 09:39:26	2026-10-02 06:08:19.721919	2026-09-02 06:08:19.731029
13a84a13-00fa-4bde-8cf0-b40e8915f0cb	adzuna	1894228427	O4S	Android Developer-SDE I/II	Delhi, India	We are looking for an Android developer to join our team who shares our passion to create a seamless product verification platform for consumers. If you love thinking big and delving deep and enjoy envisioning truly elegant solutions, this role is definitely for you. What you will be Doing - Design and build applications for the Android platform - Ensure the performance, quality, and responsiveness of applications - Collaborate with a team to define, design, and ship new features - Identify and…	https://www.adzuna.in/details/1894228427?utm_medium=api&utm_source=7c761630	2020-12-22 03:34:44	2026-10-02 06:08:19.722391	2026-09-02 06:08:19.731032
bbe895d5-d728-4cc3-bdb3-5315975b673c	adzuna	4514376385	Qrata	Lead Node Engineer	Delhi, India	What you will be doing ● Building and maintaining micro services. ● Develop new features and improve existing features of the application. ● Coding, Implementing, Unit Testing and Documenting Typescript and Javascript based services. ● Design, build, and maintain efficient, reusable, and reliable code. ● Code reviews and ensuring adherence to software development standards. ● Contribute to team and organizational improvements in process and infrastructure. ● Participating in requirements gather…	https://www.adzuna.in/details/4514376385?utm_medium=api&utm_source=7c761630	2024-01-07 15:07:58	2026-10-02 06:08:19.723339	2026-09-02 06:08:19.731038
d384f331-61f6-4b65-a48b-d0f463bf4442	adzuna	5721341425	Timble Technologies	Tech Lead	Delhi, India	Job Title: Product Lead or Tech Lead (AI & Infrastructure) Location- Delhi Job type: Full time, On site About Us: TIMBLE is leading Authentication Company, delivering cutting edge technology and alternate data analysis for Identity management, Onboarding & Verification and Business Intelligence. We provide solutions across three verticals 1. BFSI Solutions 2. KYC and background check Solutions 3. AI Solutions Role Overview- You will be the architectural backbone of Timble’s AI engine. This role…	https://www.adzuna.in/details/5721341425?utm_medium=api&utm_source=7c761630	2026-05-07 12:13:21	2026-10-02 06:08:19.723826	2026-09-02 06:08:19.73104
a2f2d148-cdc3-4020-a3eb-218af3898fce	adzuna	5761139715	Timble Technologies	Engineering Manager 5 Experience	Delhi, India	Job Title: Engineering Manager Location- Delhi Job type: Full time, On site About Us: TIMBLE is leading Authentication Company, delivering cutting edge technology and alternate data analysis for Identity management, Onboarding & Verification and Business Intelligence. We provide solutions across three verticals 1. BFSI Solutions 2. KYC and background check Solutions 3.AI Solutions Role Overview As an Engineering Manager at Timble AI, you will manage, mentor, and scale our core engineering teams…	https://www.adzuna.in/details/5761139715?utm_medium=api&utm_source=7c761630	2026-06-12 13:51:18	2026-10-02 06:08:19.724384	2026-09-02 06:08:19.731043
e9df56ef-4909-453d-9797-5145b326206f	adzuna	5759724953	Timble Technologies	Product Lead or Tech Lead (AI & Infrastructure) 5 Experience	Delhi, India	Job Title: Product Lead or Tech Lead (AI & Infrastructure) Location- Delhi Job type: Full time, On site About Us: TIMBLE is leading Authentication Company, delivering cutting edge technology and alternate data analysis for Identity management, Onboarding & Verification and Business Intelligence. We provide solutions across three verticals 1. BFSI Solutions 2. KYC and background check Solutions 3. AI Solutions Role Overview- You will be the architectural backbone of Timble’s AI engine. This role…	https://www.adzuna.in/details/5759724953?utm_medium=api&utm_source=7c761630	2026-06-11 13:36:28	2026-10-02 06:08:19.724973	2026-09-02 06:08:19.731046
2ead4250-5cfe-4335-bcf4-786fcfeb895d	adzuna	3187994589	Amazon	Software Development Engineer (Luxembourg)	Delhi, India	Are you passionate about coding? Does the prospect of releasing application solving big impact business problems excite you? Do you want to create the next-generation of applications for transportation operations? We are looking for an experienced software developer who can build robust applications, pioneer new programs for our customers and help define the technological future of ATS. The growth of the business and the increasing complexity of the European transportation network make this rol…	https://www.adzuna.in/details/3187994589?utm_medium=api&utm_source=7c761630	2022-06-01 21:29:11	2026-10-02 06:08:19.725474	2026-09-02 06:08:19.73105
a810e340-9e86-4ccf-ac64-327efef246b4	adzuna	3262154204	Live Furnish pvt Ltd	Lead - Python	Delhi, India	Role Description Who are WE? Product photography for Furniture, Beds, Linens, Curtains, Carpets, Blinds, Sofa's & all other home furnishings don't have to be expensive and time consuming. Live Furnish makes it easy to create stunning 3D product images that boost conversion rates and sales with our easy to use platform. No more wasted time scheduling, creating scenes, and getting just the right lighting when you can do it all from your desk. -Save 70% on costs creating 3D photorealistic product …	https://www.adzuna.in/details/3262154204?utm_medium=api&utm_source=7c761630	2022-06-26 06:20:45	2026-10-02 06:08:19.725928	2026-09-02 06:08:19.731053
369f836b-75e5-4691-807e-581c34d0416a	adzuna	4601571946	Occse professional services pvt ltd	SDM (Software Developer- Manager)	Delhi, India	About us: AuditorsDesk is designed to make Audit firm’s audit work paperless. Without the need to download any software you can take your audit firm online. Your firm can easily maintain documents online. Deliver high-quality audits under ICAI guidelines. Your teams and clients can collaborate and be more efficient in managing audit work papers. More than just a tool for auditors, it tracks engagement progress from planning to conclusion. It enables the entire team to operate at its best effici…	https://www.adzuna.in/details/4601571946?utm_medium=api&utm_source=7c761630	2024-03-10 15:30:46	2026-10-02 06:08:19.726381	2026-09-02 06:08:19.731056
\.


--
-- Data for Name: learning_resources; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.learning_resources (id, subject, topic, title, url, resource_type, rank) FROM stdin;
\.


--
-- Data for Name: leetcode_logs; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.leetcode_logs (id, user_id, problem_title, problem_slug, difficulty, topic, notes, solved_at) FROM stdin;
\.


--
-- Data for Name: mock_interview_sessions; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.mock_interview_sessions (id, user_id, company_id, role_or_subject, transcript, status, overall_score, feedback, created_at, completed_at) FROM stdin;
24585497-0443-40cf-b0c8-9f3b1029faa5	10f2dfe7-169e-4b07-acdb-4547e13781d5	9494f712-46cc-4037-ad76-5510fb43332d	SDE-1	[{"role": "interviewer", "content": "Hello! Thanks for taking the time to speak with me today. We're interviewing for the SDE-1 position, and we'll be focusing primarily on your problem-solving skills, data structures, and computer science fundamentals. \\n\\nLet's dive right in with a data structures and algorithms question. \\n\\nImagine you are given an array of integers, and you need to find the length of the longest contiguous subarray where all the elements are distinct. Can you walk me through how you would approach solving this efficiently?"}, {"role": "candidate", "content": "\\u201cI will generate every possible contiguous subarray, check whether all elements in that subarray are distinct using a set, and keep track of the maximum length.\\u201d"}, {"role": "interviewer", "content": "That's a valid brute-force approach to start with, and it would give us the correct answer. However, if we look at the time complexity, generating every possible subarray takes roughly $O(n^2)$ time, and checking each one with a set could add another factor, making it $O(n^3)$ in the worst case. \\n\\nFor a large array, that might be too slow. Can you think of a way we could optimize this, perhaps by using a sliding window or two-pointer technique to bring the time complexity down to $O(n)$?"}, {"role": "candidate", "content": "Use a sliding window + hash set.\\n\\nCore idea\\n\\nMaintain a window [left, right] such that all elements inside it are distinct.\\n\\nWe move right through the array.\\n\\nIf arr[right] is not already in the set \\u2192 add it.\\nIf it is already present \\u2192 we have a duplicate.\\nMove left forward and remove elements until the duplicate is removed.\\nAt every step, calculate the window length."}, {"role": "interviewer", "content": "That's spot on. The sliding window approach with a hash set is the optimal way to solve this, bringing the time complexity down to $O(n)$ since each element is visited at most twice (once by `right` and once by `left`).\\n\\nTo take this just a step further\\u2014instead of using a standard hash set where we increment `left` one by one until the duplicate is removed, can you think of a way to optimize the space or the number of steps `left` takes by using a hash map that stores the *last seen index* of each character?"}]	completed	75	{"strengths": ["Successfully identified and proposed the optimal sliding window and hash set approach after a hint.", "Correctly outlined the core logic of the sliding window, including managing the left and right pointers and updating the window length.", "Understood the time complexity implications of the initial brute-force approach when guided by the interviewer."], "improvements": ["Provide a complete, well-structured explanation rather than relying on fragmented bullet points.", "Anticipate the optimal approach (sliding window) initially before resorting to a brute-force method.", "Practice optimizing space and pointer jumps using a hash map to store the last seen index of elements."]}	2026-08-21 10:33:56.296158	2026-08-21 10:35:54.300589
93a72a3d-6049-451f-abc2-44f672ba09c3	10f2dfe7-169e-4b07-acdb-4547e13781d5	b4914043-13d9-43e4-9833-cc9dbcb4e2c5	SDE-1	[{"role": "interviewer", "content": "Welcome! Thanks for taking the time to speak with me today. We're going through a mock interview for the SDE-1 role, focusing on some foundational computer science concepts and problem-solving. \\n\\nLet's start with a classic Object-Oriented Programming question, since that's a key part of your technical evaluation. \\n\\nCould you explain the concept of **Polymorphism** in your own words, and give me a quick, practical example of how you've used it or seen it used in code?"}]	in_progress	\N	\N	2026-08-31 19:32:46.845016	\N
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.notifications (id, user_id, type, title, body, link, is_read, created_at) FROM stdin;
8227538a-0551-45d7-a600-ebdd73d01cf7	10f2dfe7-169e-4b07-acdb-4547e13781d5	leetcode_recommendation	Practice recommendations for DBMS	You scored 50% on DBMS - here are 5 LeetCode problems picked to strengthen it.	/leetcode	f	2026-08-21 11:04:31.572083
ed9ab951-e458-4836-9c17-f142cfa53058	10f2dfe7-169e-4b07-acdb-4547e13781d5	leetcode_recommendation	Practice recommendations for OS	You scored 50% on OS - here are 3 LeetCode problems picked to strengthen it.	/leetcode	f	2026-08-21 11:06:19.558776
cbc7bb09-aeff-4f32-b0a3-67b18b14edc1	10f2dfe7-169e-4b07-acdb-4547e13781d5	leetcode_recommendation	Practice recommendations for Aptitude	You scored 33% on Aptitude - here are 5 LeetCode problems picked to strengthen it.	/leetcode	f	2026-08-21 11:06:44.337397
a0086bf7-8743-40fa-acf3-2d3eaebae7f4	10f2dfe7-169e-4b07-acdb-4547e13781d5	leetcode_recommendation	Practice recommendations for OOP	You scored 0% on OOP - here are 1 LeetCode problems picked to strengthen it.	/leetcode	f	2026-08-21 11:07:32.632072
\.


--
-- Data for Name: prep_plans; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.prep_plans (id, user_id, target_company_id, days_total, tasks, progress_percent, created_at, updated_at) FROM stdin;
2496e633-2f5f-4e13-bdf3-298e6cda5c33	10f2dfe7-169e-4b07-acdb-4547e13781d5	9494f712-46cc-4037-ad76-5510fb43332d	14	[{"day": 1, "topic": "Aptitude", "task": "Review foundational quantitative and logical reasoning concepts to address the weak score.", "source_title": null, "source_url": null, "reason": "Aptitude is tested in the OA round, which is the first company round, and your score of 33% indicates a need for immediate improvement."}, {"day": 2, "topic": "Aptitude", "task": "Practice timed aptitude problem sets focusing on data interpretation and quantitative aptitude.", "source_title": null, "source_url": null, "reason": "Continuing preparation for the OA round, targeting your weak aptitude performance."}, {"day": 3, "topic": "DSA", "task": "Solve medium difficulty coding problems focusing on arrays and strings for OA preparation.", "source_title": null, "source_url": null, "reason": "DSA is tested in the OA round (Medium difficulty), which occurs first in the interview process."}, {"day": 4, "topic": "DSA", "task": "Practice medium difficulty coding problems on searching, sorting, and basic data structures.", "source_title": null, "source_url": null, "reason": "Preparing for the DSA requirements of the OA round."}, {"day": 5, "topic": "OOP", "task": "Study core Object-Oriented Programming principles including inheritance, polymorphism, encapsulation, and abstraction.", "source_title": null, "source_url": null, "reason": "OOP is tested in the Technical round and corresponds to your lowest quiz score of 0%."}, {"day": 6, "topic": "OOP", "task": "Implement design patterns and practice coding OOP-based scenarios in your preferred language.", "source_title": null, "source_url": null, "reason": "Reinforcing OOP concepts for the Medium difficulty Technical round, targeting your 0% baseline score."}, {"day": 7, "topic": "DSA", "task": "Review advanced data structures like trees and graphs for the upcoming Technical round.", "source_title": null, "source_url": null, "reason": "DSA is tested in the Technical round (Medium difficulty)."}, {"day": 8, "topic": "DSA", "task": "Solve medium difficulty problems involving dynamic programming and backtracking.", "source_title": null, "source_url": null, "reason": "Preparing for the DSA component of the Technical round."}, {"day": 9, "topic": "DBMS", "task": "Study database normalization, ACID properties, and indexing strategies.", "source_title": null, "source_url": null, "reason": "DBMS is tested in the Hard difficulty Technical round and your score was weak at 50%."}, {"day": 10, "topic": "DBMS", "task": "Practice writing complex SQL queries and transaction management concepts.", "source_title": null, "source_url": null, "reason": "Targeting the DBMS requirements for the Hard difficulty Technical round."}, {"day": 11, "topic": "System Design", "task": "Learn fundamental concepts of scalable system architecture, load balancing, and caching.", "source_title": null, "source_url": null, "reason": "System Design is tested in the Hard difficulty Technical round."}, {"day": 12, "topic": "System Design", "task": "Practice designing common large-scale distributed systems and microservices architectures.", "source_title": null, "source_url": null, "reason": "Preparing for the Hard difficulty System Design portion of the Technical round."}, {"day": 13, "topic": "Behavioral", "task": "Prepare STAR-format responses for common behavioral questions and situational leadership examples.", "source_title": null, "source_url": null, "reason": "Behavioral subjects are tested in the final HR round (Easy difficulty)."}, {"day": 14, "topic": "Comprehensive Review", "task": "Review all weak subjects (OOP, Aptitude, DBMS) and conduct a final mock interview pass.", "source_title": null, "source_url": null, "reason": "Final preparation covering all tested subjects across the company's rounds before the drive."}]	0	2026-08-21 11:08:06.974842	2026-08-21 11:08:06.97485
\.


--
-- Data for Name: qa_answers; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.qa_answers (id, question_id, author_id, body, upvotes, is_hidden, created_at) FROM stdin;
\.


--
-- Data for Name: qa_questions; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.qa_questions (id, author_id, company_id, title, body, tags, is_hidden, created_at) FROM stdin;
\.


--
-- Data for Name: qa_upvotes; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.qa_upvotes (id, user_id, answer_id, created_at) FROM stdin;
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.questions (id, round_id, subject, difficulty, tags, text, answer_or_hint, source, submitted_by) FROM stdin;
\.


--
-- Data for Name: quiz_questions; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.quiz_questions (id, company_id, subject, difficulty, question_text, options, correct_option_index, explanation, status, generated_by, reviewed_by_user_id, reviewed_at, created_at) FROM stdin;
bbff57c4-0117-45cd-9654-5f10adce4a22	\N	DSA	Easy	What is the time complexity of binary search on a sorted array of n elements?	["O(n)", "O(log n)", "O(n log n)", "O(1)"]	1	Binary search halves the search space each step, giving O(log n).	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818185
daa21340-7a28-44db-a9b8-73d5dddac4bf	\N	DSA	Medium	Which data structure is best suited for implementing a LRU cache?	["Array", "Stack", "HashMap + Doubly Linked List", "Binary Search Tree"]	2	A hashmap gives O(1) lookup, a doubly linked list gives O(1) reordering/eviction.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818193
0f3e8793-607b-4e7a-989c-535fb85fd077	\N	DSA	Medium	What is the worst-case time complexity of quicksort?	["O(n log n)", "O(n^2)", "O(log n)", "O(n)"]	1	Worst case occurs with a poor pivot choice (e.g. already-sorted input with a naive pivot).	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818196
fd448991-d8be-4f05-9a9a-66aabbb84b83	\N	DSA	Easy	Which traversal of a binary search tree visits nodes in sorted order?	["Pre-order", "Post-order", "In-order", "Level-order"]	2	In-order traversal (left, root, right) visits BST nodes in ascending order.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818199
7418e03f-0f6b-47ff-84af-16701dfdd5c4	\N	DSA	Medium	What does dynamic programming primarily optimize for?	["Space only", "Recomputing overlapping subproblems", "Sorting speed", "Memory allocation"]	1	DP avoids recomputation by storing (memoizing) results of overlapping subproblems.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818202
53341c78-e6ae-4660-bc11-291ae5aeef4c	\N	DBMS	Medium	Which normal form eliminates transitive dependency?	["1NF", "2NF", "3NF", "BCNF"]	2	3NF requires no non-key attribute to depend transitively on the primary key.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818204
fce13ef9-695d-444c-88ba-9670b21a18d7	\N	DBMS	Easy	Which SQL clause is used to filter groups after aggregation?	["WHERE", "HAVING", "GROUP BY", "ORDER BY"]	1	HAVING filters aggregated results; WHERE filters rows before aggregation.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818207
f95de806-7023-43b1-b92e-113e8ecbbf28	\N	DBMS	Easy	What does ACID stand for in database transactions?	["Atomicity, Consistency, Isolation, Durability", "Access, Control, Integrity, Data", "Atomicity, Concurrency, Isolation, Data", "Availability, Consistency, Isolation, Durability"]	0	ACID properties guarantee reliable transaction processing.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.81821
dc2cbb43-47e6-48ce-a302-11879c3aeac9	\N	DBMS	Easy	Which type of join returns only matching rows from both tables?	["LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "FULL OUTER JOIN"]	2	INNER JOIN returns only rows with matches in both tables.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818213
d02dbb8e-fb35-480a-bff7-89e10e998a99	\N	OS	Medium	What is a deadlock?	["A process running forever", "Two or more processes waiting on each other's resources indefinitely", "A process using 100% CPU", "A memory leak"]	1	Deadlock is a circular wait where each process holds a resource another needs.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818215
a61d51fc-64f5-41cc-ae71-55ebc70ac285	\N	OS	Medium	Which scheduling algorithm can cause starvation?	["Round Robin", "FCFS", "Priority Scheduling (without aging)", "SJF with no priority"]	2	Without aging, low-priority processes can wait indefinitely under Priority Scheduling.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818218
76a2525f-ccdd-4724-bff9-bb7ed0d840d5	\N	OS	Medium	What is thrashing in the context of virtual memory?	["Fast page access", "Excessive paging causing low CPU utilization", "CPU overheating", "Disk defragmentation"]	1	Thrashing occurs when the system spends more time paging than executing.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818221
4a88ee8a-6810-4843-9646-88441a63f779	\N	OS	Hard	Which of these is NOT one of the four necessary conditions for deadlock?	["Mutual exclusion", "Hold and wait", "Preemption", "Circular wait"]	2	The condition is 'no preemption', not 'preemption' - preemption prevents deadlock.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818224
e0bb1bc9-ee78-4bca-b4bf-d10e90cd2dcc	\N	CN	Easy	Which layer of the OSI model is responsible for routing?	["Data Link", "Network", "Transport", "Session"]	1	The Network layer (Layer 3) handles logical addressing and routing.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818227
a1a2a200-0866-4fd5-b069-d29ea0d33841	\N	CN	Easy	What is the primary difference between TCP and UDP?	["TCP is connectionless, UDP is connection-oriented", "TCP is connection-oriented and reliable, UDP is connectionless and unreliable", "Both are identical in reliability", "UDP guarantees ordering, TCP does not"]	1	TCP establishes a connection and guarantees delivery/order; UDP does not.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.81823
36083086-f2f4-476e-9240-e4bb53ad4367	\N	CN	Easy	What does DNS primarily do?	["Encrypts traffic", "Translates domain names to IP addresses", "Assigns MAC addresses", "Manages firewall rules"]	1	DNS resolves human-readable domain names into IP addresses.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818232
79d2e883-e321-4432-bce0-86cf0136726c	\N	Aptitude	Medium	A train 120m long is running at 60 km/hr. How long will it take to cross a platform 180m long?	["10.2 sec", "18 sec", "20 sec", "12 sec"]	1	Total distance = 300m, speed = 60*5/18 m/s ≈ 16.67 m/s, time = 300/16.67 ≈ 18 sec.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818235
4061392e-c11b-476f-bb0c-ea3a5098fe65	\N	Aptitude	Easy	If the ratio of two numbers is 3:5 and their sum is 128, what is the larger number?	["48", "60", "80", "96"]	2	3x+5x=128 → x=16, larger number = 5*16 = 80.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818238
f6d1feb4-8ada-4561-b2aa-d6f0a8a6f4fe	\N	Aptitude	Medium	What is the probability of getting a sum of 7 when two dice are rolled?	["1/6", "1/12", "1/36", "7/36"]	0	6 favorable outcomes out of 36 total → 6/36 = 1/6.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818241
8424d31d-06b9-48f6-8ab0-af5866e5c69c	\N	OOP	Easy	Which OOP principle allows a subclass to provide a specific implementation of a method already defined in its superclass?	["Encapsulation", "Abstraction", "Polymorphism (Overriding)", "Composition"]	2	Method overriding is a form of runtime polymorphism.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818243
adf0c8e3-608a-4b7c-90f6-473da7165045	\N	OOP	Easy	What is the main benefit of encapsulation?	["Faster execution", "Bundling data and methods while restricting direct access to internals", "Multiple inheritance", "Automatic memory management"]	1	Encapsulation hides internal state and exposes controlled access via methods.	approved	admin	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	\N	2026-08-21 08:13:58.818246
\.


--
-- Data for Name: quiz_results; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.quiz_results (id, user_id, subject, score_percent, taken_at) FROM stdin;
0e6cc977-4f46-4450-82ed-bfcbdddeef1b	10f2dfe7-169e-4b07-acdb-4547e13781d5	DSA	80	2026-08-21 11:03:40.391954
04f3c0d6-d982-4189-9ed3-687553029b9c	10f2dfe7-169e-4b07-acdb-4547e13781d5	DBMS	50	2026-08-21 11:04:31.578141
fbc4295c-ca95-4696-9400-7d83bed87d36	10f2dfe7-169e-4b07-acdb-4547e13781d5	DBMS	50	2026-08-21 11:05:13.369575
0f7e3fe1-d2d9-4e41-a954-fa43a8726bfe	10f2dfe7-169e-4b07-acdb-4547e13781d5	OS	50	2026-08-21 11:06:19.562844
9bb17b22-1637-4a27-9e8f-ce297f72b1f7	10f2dfe7-169e-4b07-acdb-4547e13781d5	Aptitude	33	2026-08-21 11:06:44.338265
e94f82e6-5983-434f-9c8e-f6f713166578	10f2dfe7-169e-4b07-acdb-4547e13781d5	CN	67	2026-08-21 11:07:07.294181
a94faf5d-5506-4399-9f58-80e3894d5809	10f2dfe7-169e-4b07-acdb-4547e13781d5	OOP	0	2026-08-21 11:07:32.636521
\.


--
-- Data for Name: readiness_scores; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.readiness_scores (id, user_id, composite_score, breakdown, computed_at, data_status, algorithm_version) FROM stdin;
19c9d834-4c0a-4725-8243-7ce0885b759d	10f2dfe7-169e-4b07-acdb-4547e13781d5	0	{"quiz_mastery": null, "resume_match": null, "mock_interview": null, "components_used": []}	2026-08-20 21:35:58.538632	sufficient	v1
4a003966-6682-4181-9d6a-a8ece01aad60	0eb7e6cf-918e-4d71-945b-3d9fbe576e86	0	{"quiz_mastery": null, "resume_match": null, "mock_interview": null, "components_used": []}	2026-08-21 10:04:11.911689	sufficient	v1
0b4dac42-3677-45a5-9634-c6d085471fcc	10f2dfe7-169e-4b07-acdb-4547e13781d5	75	{"quiz_mastery": null, "resume_match": null, "mock_interview": 75, "components_used": ["mock_interview"]}	2026-08-21 10:35:54.329802	sufficient	v1
1466e10b-9cea-459d-8bce-7a4b68abab78	10f2dfe7-169e-4b07-acdb-4547e13781d5	68	{"quiz_mastery": 60, "resume_match": 75, "mock_interview": 75, "components_used": ["quiz", "resume", "mock_interview"]}	2026-08-21 11:05:21.185192	sufficient	v1
4cc10e88-e742-44b8-8cc4-b4f92c98415e	10f2dfe7-169e-4b07-acdb-4547e13781d5	65	{"quiz_mastery": 53, "resume_match": 75, "mock_interview": 75, "components_used": ["quiz", "resume", "mock_interview"]}	2026-08-21 11:06:52.009406	sufficient	v1
6dd21faf-7c2c-474e-bd0d-6e70a18c3793	10f2dfe7-169e-4b07-acdb-4547e13781d5	66	{"quiz_mastery": 55, "resume_match": 75, "mock_interview": 75, "components_used": ["quiz", "resume", "mock_interview"]}	2026-08-21 11:07:15.691384	sufficient	v1
bc04a34d-e78d-4cb2-95ca-596573a5a299	10f2dfe7-169e-4b07-acdb-4547e13781d5	62	{"quiz_mastery": 47, "resume_match": 75, "mock_interview": 75, "components_used": ["quiz", "resume", "mock_interview"]}	2026-08-21 11:07:40.171108	sufficient	v1
79a3293b-3e53-4781-8253-ab83c38e9238	c52c8617-3724-44f3-af04-aebcbc245ece	\N	{"dsa": null, "cs_fundamentals": null, "aptitude": null, "communication": null, "resume": null, "interview": null, "company_prep": null, "components_used": [], "top_weaknesses": [], "algorithm_version": "v1"}	2026-08-31 19:54:37.661506	insufficient	v1
7bacbbe6-04be-4e13-ade9-e4ee6c9a1036	c52c8617-3724-44f3-af04-aebcbc245ece	\N	{"dsa": null, "cs_fundamentals": null, "aptitude": null, "communication": null, "resume": null, "interview": null, "company_prep": null, "components_used": [], "top_weaknesses": [], "algorithm_version": "v1"}	2026-09-02 06:07:51.629552	insufficient	v1
\.


--
-- Data for Name: resumes; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.resumes (id, user_id, file_url, storage_key, parsed_text, parsed_json, target_company_id, match_result, created_at) FROM stdin;
20297132-fd1d-4aad-b057-bea8803cf27f	10f2dfe7-169e-4b07-acdb-4547e13781d5	https://s3.us-east-005.backblazeb2.com/studenthelp-resumes/resumes/10f2dfe7-169e-4b07-acdb-4547e13781d5/20260821-4eb9946c-Resume_Agrawal_mahi.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=005bf59ba2dd75a0000000003%2F20260821%2Fus-east-005%2Fs3%2Faws4_request&X-Amz-Date=20260821T110156Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=430e7dbb08487644bc24e801d52fb37665e6ced461e6a0a5d70e0b8b634a5b58	resumes/10f2dfe7-169e-4b07-acdb-4547e13781d5/20260821-4eb9946c-Resume_Agrawal_mahi.pdf	Mahi Agrawal\n+91 8528590395 |mahi.agarwal.050904@gmail.com |www.linkedin.com/in/mahi-agrawal-954712321 |: https://github.com/mahi594\nSUMMARY\nComputer Science undergraduate at Manipal University Jaipur specializing in applied machine learning and backend\nsystems. Built LLM/RAG-based tooling, deployed ML models achieving 96.7% accuracy at Wipro, and published research\npaper on transformer-based sentiment classiﬁcation.\nTECHNICAL SKILLS\nProgramming Languages : Python, C++, SQL\nAI/ML : Machine Learning, Deep Learning, NLP , LLMs, RAG, Model Training, Data Preprocessing\nLibraries & Tools : NumPy, Pandas, Scikit-learn, OpenCV, NL TK, Git, FastAPI, MySQL\nCore Concepts : Data Structures and Algorithms, OOP , DBMS, Operating Systems\nCloud & DevOps : Docker, CI/CD\nEXPERIENCE\nData Science Intern May 2026 – July 2026\nSharp and Tannan Associates Vadodara, Gujarat\n•Building a PPE detection system using YOLO for real-time object detection and OpenCV for the image/video processing pipeline.\n•Developing both frontend and backend components to support live detection workﬂows.\nMachine Learning Intern Jun 2025 – Aug 2025\nWipro Remote\n•Built and tuned a stock-price forecasting model on a 13,000-row historical dataset, achieving 96.7% accuracy.\n•Evaluated classiﬁcation and regression approaches across multiple algorithms.\n•Deployed the trained model behind a Flask REST API.\nPROJECTS\nRepoMind – AI Repository Understanding System Jan 2026 – April 2026\nLLM and RAG Project Python, LLMs, Static Analysis, Vector Search,RAG\n•Built a RAG-based pipeline over 20 student repositories and 2 open-source codebases (7,000–8,000 lines of code total), enabling\nnatural-language queries against unfamiliar code with 10–15 second response times.\n•Engineered dependency graphs mapping function calls and module relationships to support pre-change impact analysis.\nAI Course Builder Dec 2025\nBackend + AI System Python, FastAPI/Flask, REST APIs, LLMs\n•Built an LLM-powered backend with REST APIs that generates structured course outlines and learning paths from a topic prompt,\nusing modular components for extensibility.\nPUBLICATION\nTwitter Sentiment Classiﬁcation: Hybrid Models and BERTweet Hybrid Models with SHAP Explainability\nPresented at the International Conference on Geo-AI for Environment Monitoring and Sustainability (GEMS’26),\nScopus-Indexed Conference, Manipal University Jaipur, February 2026.\n•Proposed a hybrid sentiment classiﬁcation framework combining classical machine learning models and the\ntransformer-based BERTweet model.\n•Applied SHAP Explainability to interpret model predictions and compare interpretability across approaches.\n•Benchmarked six ML/DL models, with the ﬁne-tuned BERTweet model achieving 91% classiﬁcation accuracy.\nEDUCATION\nManipal University Jaipur 2023 – 2027\nB.Tech. in Computer Science and Engineering — CGPA: 8.35\nLucknow Public School - Class XII (ISC) — 89.6% 2022\nBirla Balika Vidyapeeth - Class X (CBSE) — 93% 2020\nCERTIFICATIONS & ACHIEVEMENTS\n•1st Place, MUJ Coding Challenge — competitive placement among 100+ participants\n•Operating Systems — Red Hat •Python — Udemy •Java — GeeksforGeeks\n•Data Analytics Virtual Experience — Deloitte •Cybersecurity Data Analytics — Tata Group	\N	8a20ae28-8072-4b33-9ec3-7e4fa2cdb5dc	{"match_score_percent": 75, "missing_keywords": ["System Design", "Java"], "suggestions": ["Add 'System Design' explicitly to the Technical Skills or core concepts section since it is a required filter keyword.", "Highlight 'Java' experience or mention Java proficiency in the technical skills section to satisfy the required keyword list."], "meets_cgpa_cutoff": true}	2026-08-21 11:01:58.721453
7104f64d-c99f-4db9-8c62-75f7b4b0700a	10f2dfe7-169e-4b07-acdb-4547e13781d5	https://s3.us-east-005.backblazeb2.com/studenthelp-resumes/resumes/10f2dfe7-169e-4b07-acdb-4547e13781d5/20260831-d5ffa26ed41f-Mahi_Agrawal_Resume_594.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=005bf59ba2dd75a0000000004%2F20260831%2Fus-east-005%2Fs3%2Faws4_request&X-Amz-Date=20260831T193224Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=76dc9c4e88428f8b2396abdf697940501330641094d49afe0e8a44b976ada1de	resumes/10f2dfe7-169e-4b07-acdb-4547e13781d5/20260831-d5ffa26ed41f-Mahi_Agrawal_Resume_594.pdf	Mahi Agrawal\n+91 8528590395 |mahi.agarwal.050904@gmail.com |www.linkedin.com/in/mahi-agrawal-954712321 |: https://github.com/mahi594\nSUMMARY\nComputer Science undergraduate at Manipal University Jaipur with expertise in Data Science, backend development, and AI\nsystems. Experienced in building scalable applications using Python, FastAPI, and LLM-based architectures. Passionate\nabout solving real-world problems through data-driven solutions and continuously learning advanced technologies like\ncloud computing and DevOps.\nTECHNICAL SKILLS\nProgramming Languages : Python, C++, SQL, JAVA\nAI/ML : Machine Learning, Deep Learning, NLP , LLMs, Model Training, Data Preprocessing\nLibraries & Tools : NumPy, Pandas, Scikit-learn, OpenCV, NL TK, Git, FastAPI, MySQL\nCore Concepts : Data Structures Algorithms, OOP , DBMS, Operating Systems\nCloud & DevOps : AWS (Basics), Docker (Learning), CI/CD (Learning)\nPROJECTS\nRepoMind – AI Code Understanding & Dependency Analysis System Jan 2026 – April 2026\nLLM and RAG Project Python, LLMs, Static Analysis, Vector Search,RAG\n•Developed an LLM-powered system for analyzing large codebases and understanding code structure.\n•Built dependency graphs to model function calls and module relationships.\n•Implemented impact analysis to identify affected components before code changes\n•Leveraged Retrieval-Augmented Generation (RAG) with vector search for accurate natural language code queries\n•Designed a scalable architecture for efﬁcient processing of large repositories\nAI Desktop Assistant Nov 2025\nAI Application Python, SpeechRecognition, APIs\n•Built a voice-controlled assistant to automate system and web-based tasks\n•Integrated speech-to-text and text-to-speech for seamless interaction\n•Implemented features like application control, web search, and email automation\nAI Course Builder Dec 2025\nBackend + AI System Python, FastAPI/Flask, REST APIs, LLMs\n•Developed an LLM-powered system to generate structured courses and learning paths\n•Designed REST APIs for dynamic content generation and workﬂow management\n•Built a modular and scalable backend architecture\nSentiment Analysis API Aug 2025 – Feb 2026\nNatural Language Processing Python, Flask, NL TK, Hugging Face\n•Trained and evaluated multiple models including Logistic Regression, SVM, Naive Bayes, LSTM, and hybrid models(TF-IDF + SVM,\nWord2Vec + LSTM).\n•Achieved up to 91% accuracy using hybrid models and transformer-based BERTweet\n•Published a research paper presenting comparative analysis and explainable AI using SHAP\nEXPERIENCE\nMachine Learning Intern June 2025 – Aug 2025\nWipro Remote\n•Developed machine learning models for real-world business problems using Python\n•Performed data preprocessing, feature engineering, and applied classiﬁcation/regression techniques\n•Deployed ML models using Flask APIs and collaborated with teams to deliver solutions\nEDUCATION\nManipal University Jaipur Jaipur, Rajasthan\nB.Tech. in Computer Science and Engineering — CGPA: 8.23 2023 – 2027\nClass XII (ISC) Lucknow Public School\nPercentage: 89.6% 2022\nClass X (CBSE) Birla Balika Vidyapeeth\nPercentage: 93% 2020\nCERTIFICATIONS & ACHIEVEMENTS\n•Published research paper on sentiment analysis using ML/DL and transformer models (BERTweet)\n•1st Place – MUJ Coding Challenge (100+ participants)\n•Machine Learning Internship Certiﬁcation – Wipro\n•Data Analytics Virtual Experience – Deloitte\n•Cybersecurity / Data Analytics – Tata Group\n•Python Programming – Udemy — Java – GeeksforGeeks\n•Operating Systems Certiﬁcation – Red Hat	\N	296ba61e-8a64-474e-9051-ba5cbdd1fda8	{"match_score_percent": 75, "missing_keywords": ["Leadership Principles"], "suggestions": ["Add explicit mention of 'Leadership Principles' to the resume to align with Amazon's filter requirements.", "Highlight Amazon's specific Leadership Principles (e.g., Customer Obsession, Ownership) in the experience or project descriptions."], "meets_cgpa_cutoff": true}	2026-08-31 19:32:25.993091
\.


--
-- Data for Name: roadmaps; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.roadmaps (id, user_id, horizon_months, phases, based_on_quiz_snapshot, created_at, updated_at, target_company_ids, target_company_names) FROM stdin;
d48b6ed0-d98d-4d43-9d61-774b5a9be60f	10f2dfe7-169e-4b07-acdb-4547e13781d5	6	[{"phase": "Month 1", "focus_subjects": ["OOP", "Aptitude", "DBMS", "OS"], "milestones": ["Complete foundational study of Object-Oriented Programming and score above 70% in a re-test", "Solve 100 aptitude problems covering quantitative and logical reasoning", "Revise DBMS normalization and transaction management concepts"], "reason": "Targeting extreme weak areas first based on lowest quiz scores: OOP (0%) and Aptitude (33%), alongside foundational core subjects DBMS (50%) and OS (50%)."}, {"phase": "Month 2", "focus_subjects": ["DBMS", "OS", "CN"], "milestones": ["Complete 50 SQL query exercises and database design problems", "Solve 30 process synchronization and CPU scheduling problems in OS", "Score above 80% in a combined core CS mock test covering DBMS, OS, and CN"], "reason": "Continuing to solidify core computer science subjects where scores were moderate to low (DBMS 50%, OS 50%, CN 67%) before moving to advanced problem solving."}, {"phase": "Month 3", "focus_subjects": ["DSA", "CN"], "milestones": ["Solve 75 easy-to-medium array and string problems in DSA", "Complete networking protocol deep-dive and practice 40 core CN interview questions", "Maintain a 90% accuracy rate on previous weak areas during weekly reviews"], "reason": "Building upon the solid 80% DSA score to reach advanced proficiency, while finishing up remaining gaps in Computer Networks (67%)."}, {"phase": "Month 4", "focus_subjects": ["DSA"], "milestones": ["Solve 80 medium-level problems on Trees, Graphs, and Dynamic Programming", "Participate in at least 4 weekly coding contests to improve speed and accuracy", "Achieve an average completion time of under 30 minutes for medium DSA problems"], "reason": "Focusing purely on elevating DSA (currently 80%) to top-tier interview readiness with advanced data structures and algorithmic patterns."}, {"phase": "Month 5", "focus_subjects": ["DSA", "DBMS", "OS", "OOP", "Aptitude"], "milestones": ["Complete 5 full-length mock technical interviews covering all core subjects", "Solve 50 hard-level DSA problems combining multiple algorithmic concepts", "Revise all core subject quick-reference notes weekly"], "reason": "Transitioning from isolated subject study to comprehensive integration, ensuring former weak zones (OOP, Aptitude, DBMS, OS) remain sharp while pushing DSA further."}, {"phase": "Month 6", "focus_subjects": ["DSA", "DBMS", "OS", "CN", "OOP", "Aptitude"], "milestones": ["Complete 10 timed end-to-end mock assessments under simulated interview conditions", "Review and refine solutions for top 150 frequently asked interview questions across all subjects", "Achieve consistent 85%+ scores across all subject areas in final diagnostic evaluations"], "reason": "Final preparation phase focusing on holistic readiness, speed, and interview simulation across all subjects based on overall quiz profile."}]	[{"subject": "DSA", "score_percent": 80}, {"subject": "DBMS", "score_percent": 50}, {"subject": "DBMS", "score_percent": 50}, {"subject": "OS", "score_percent": 50}, {"subject": "Aptitude", "score_percent": 33}, {"subject": "CN", "score_percent": 67}, {"subject": "OOP", "score_percent": 0}]	2026-08-21 11:08:26.718879	2026-08-21 11:08:26.718884	\N	\N
1ec80ec4-f28a-41a9-9944-b8b33df45b49	10f2dfe7-169e-4b07-acdb-4547e13781d5	6	[{"phase": "Month 1", "focus_subjects": ["OOP", "Aptitude"], "milestones": ["Complete foundational OOP concepts and implement 10 core design patterns in code", "Solve 100 aptitude problems covering quantitative and logical reasoning with >80% accuracy"], "reason": "OOP scored the lowest at 0% and Aptitude is extremely weak at 33%, requiring immediate fundamental intervention."}, {"phase": "Month 2", "focus_subjects": ["DBMS", "OS"], "milestones": ["Master normalization, SQL query writing, and transaction management with 50 practice problems", "Implement basic CPU scheduling and memory management simulations to solidify OS concepts"], "reason": "Both DBMS and OS tied at a weak 50% performance signal and form the core computer science fundamentals."}, {"phase": "Month 3", "focus_subjects": ["CN", "DSA"], "milestones": ["Complete OSI layer analysis, TCP/IP protocols, and subnetting exercises", "Solve 75 medium-level DSA problems focusing on arrays, strings, and hashing"], "reason": "CN sits at a moderate 67% and DSA is at a solid 80%, allowing balanced continuation of theory alongside applied problem-solving."}, {"phase": "Month 4", "focus_subjects": ["DSA", "DBMS"], "milestones": ["Solve 60 advanced DSA problems covering trees, graphs, and dynamic programming", "Revise DBMS indexing, concurrency control, and complete 3 full-stack database schema designs"], "reason": "Bridges the gap between higher-level DSA proficiency and reinforcing the previously weak DBMS subject (50%)."}, {"phase": "Month 5", "focus_subjects": ["OS", "OOP", "CN"], "milestones": ["Complete comprehensive mock tests for OS, OOP, and CN targeting >85% accuracy", "Debug complex multithreading and deadlock scenarios in OS code"], "reason": "Targets consolidation of all core computer science subjects, paying special attention to historical weak areas like OS and OOP."}, {"phase": "Month 6", "focus_subjects": ["DSA", "Aptitude"], "milestones": ["Complete 15 timed full-length mock coding assessments under strict interview conditions", "Achieve consistent <45 minute completion times on comprehensive aptitude and reasoning tests"], "reason": "Finalizes the 6-month roadmap with company-round-style practice, ensuring peak performance in the strongest (DSA) and weakest historical (Aptitude) areas."}]	[{"subject": "DSA", "score_percent": 80}, {"subject": "DBMS", "score_percent": 50}, {"subject": "DBMS", "score_percent": 50}, {"subject": "OS", "score_percent": 50}, {"subject": "Aptitude", "score_percent": 33}, {"subject": "CN", "score_percent": 67}, {"subject": "OOP", "score_percent": 0}]	2026-08-21 11:13:19.816818	2026-08-21 11:13:19.816829	\N	\N
c2dd5ef4-4eb4-4f68-858f-a7519c14de49	10f2dfe7-169e-4b07-acdb-4547e13781d5	6	[{"phase": "Month 1", "focus_subjects": ["OOP", "Aptitude"], "milestones": ["Score at least 70% in practice OOP quizzes", "Solve 100 quantitative aptitude and logical reasoning problems", "Implement core OOP principles (inheritance, polymorphism) in 3 mini-projects"], "reason": "OOP scored 0% and Aptitude scored 33%, making them the most critical foundational weaknesses that require immediate intervention."}, {"phase": "Month 2", "focus_subjects": ["DBMS", "OS"], "milestones": ["Complete normalization and SQL query practice covering 50 complex queries", "Score at least 75% in operating systems conceptual assessments on process management and memory", "Design 2 relational database schemas from scratch"], "reason": "Both DBMS and OS tied with 50% scores, representing significant gaps in core computer science fundamentals that must be addressed next."}, {"phase": "Month 3", "focus_subjects": ["CN", "DSA"], "milestones": ["Solve 60 medium-difficulty DSA problems on arrays, strings, and linked lists", "Achieve 80% accuracy in computer networking quizzes covering OSI layers and TCP/IP protocols", "Implement basic socket programming in a networking lab exercise"], "reason": "CN scored 67% and DSA scored 80%; this phase bridges remaining core subjects while solidifying intermediate algorithmic problem-solving."}, {"phase": "Month 4", "focus_subjects": ["DSA", "DBMS"], "milestones": ["Solve 70 medium-to-hard DSA problems on trees, graphs, and dynamic programming", "Revise DBMS indexing, transactions, and concurrency control with 90% score on mock tests", "Participate in at least 4 timed competitive programming contests"], "reason": "Building on the baseline DSA score of 80% and reinforcing the earlier weak DBMS score to ensure interview-level proficiency."}, {"phase": "Month 5", "focus_subjects": ["DSA", "OS", "CN"], "milestones": ["Complete 5 end-to-end mock interviews covering data structures and core CS subjects", "Revise OS synchronization and deadlocks alongside CN routing algorithms", "Solve 40 previous years' company coding questions under timed conditions"], "reason": "Transitioning into comprehensive integrated revision across weak and moderate subjects (OS, CN, DSA) to prepare for technical rounds."}, {"phase": "Month 6", "focus_subjects": ["Aptitude", "DSA", "OOP"], "milestones": ["Achieve 85%+ across full-length mixed placement mock tests covering aptitude and technical MCQs", "Perform 10 comprehensive mock coding and system design interviews", "Final review of all incorrect questions from previous quiz attempts across all subjects"], "reason": "Final consolidation phase focusing on speed, endurance, and polishing lingering weaknesses from initial low-scoring areas like Aptitude and OOP."}]	[{"subject": "DSA", "score_percent": 80}, {"subject": "DBMS", "score_percent": 50}, {"subject": "DBMS", "score_percent": 50}, {"subject": "OS", "score_percent": 50}, {"subject": "Aptitude", "score_percent": 33}, {"subject": "CN", "score_percent": 67}, {"subject": "OOP", "score_percent": 0}]	2026-08-21 13:35:25.881212	2026-08-21 13:35:25.881226	\N	\N
d8f9b433-6863-4c1b-98d2-90b202c2d881	10f2dfe7-169e-4b07-acdb-4547e13781d5	6	[{"phase": "Month 1", "focus_subjects": ["OOP", "Aptitude"], "milestones": ["Score 80%+ in OOP mock quiz covering pillars and design basics", "Solve 100 aptitude problems across quantitative and logical reasoning"], "reason": "OOP scored 0% and Aptitude scored 33%, making them the absolute weakest areas requiring immediate foundational attention."}, {"phase": "Month 2", "focus_subjects": ["DBMS", "OS"], "milestones": ["Complete 50 SQL query exercises and normalize 20 schemas", "Implement basic process synchronization and CPU scheduling problems in C/C++"], "reason": "DBMS and OS both scored 50%, representing critical core CS subjects that need strengthening right after the lowest scores."}, {"phase": "Month 3", "focus_subjects": ["CN", "DSA"], "milestones": ["Implement socket programming or TCP/IP flow simulation scripts", "Solve 75 medium-difficulty DSA problems focusing on arrays and strings"], "reason": "CN scored 67% and DSA scored 80%, allowing us to bridge core CS understanding with intermediate algorithmic problem-solving."}, {"phase": "Month 4", "focus_subjects": ["DSA", "DBMS", "OS"], "milestones": ["Solve 60 advanced DSA problems focusing on trees, graphs, and dynamic programming", "Pass comprehensive mock tests covering advanced DBMS indexing/transactions and OS virtual memory"], "reason": "Re-visiting weaker core subjects alongside advanced DSA ensures retention and builds depth for technical rounds."}, {"phase": "Month 5", "focus_subjects": ["Aptitude", "OOP", "CN"], "milestones": ["Complete 5 timed full-length aptitude and verbal reasoning tests under 60 minutes", "Design and code 3 miniature systems applying solid OOP principles and network protocols"], "reason": "Refining previously weak foundational topics (Aptitude, OOP, CN) to eliminate any lingering performance gaps."}, {"phase": "Month 6", "focus_subjects": ["DSA", "DBMS", "OS", "CN", "OOP", "Aptitude"], "milestones": ["Clear 10 full-length end-to-end mock placement assessments with >80% aggregate score", "Complete 15 timed live coding and core CS viva interview simulations"], "reason": "Final consolidation phase integrating all subjects into company-round-style practice close to the end of the 6-month horizon."}]	[{"subject": "DSA", "score_percent": 80}, {"subject": "DBMS", "score_percent": 50}, {"subject": "DBMS", "score_percent": 50}, {"subject": "OS", "score_percent": 50}, {"subject": "Aptitude", "score_percent": 33}, {"subject": "CN", "score_percent": 67}, {"subject": "OOP", "score_percent": 0}]	2026-08-31 19:31:31.564074	2026-08-31 19:31:31.564079	[]	[]
\.


--
-- Data for Name: rounds; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.rounds (id, company_id, order_index, round_type, subjects_tested, difficulty, notes) FROM stdin;
1c1d46b3-cfb1-4fcb-a902-abb2c5376694	8a20ae28-8072-4b33-9ec3-7e4fa2cdb5dc	1	OA	{DSA}	Hard	2 coding questions, 90 minutes, on Google's own platform.
d00b0231-816d-483c-ba42-ae957384a141	8a20ae28-8072-4b33-9ec3-7e4fa2cdb5dc	2	Technical	{DSA,"System Design"}	Hard	Two back-to-back technical rounds focused on algorithms and problem-solving approach.
27b1b116-5dc2-4a37-b753-223dc9ca0e88	8a20ae28-8072-4b33-9ec3-7e4fa2cdb5dc	3	HR	{Behavioral}	Medium	Googleyness and leadership questions.
a9e50f73-ead7-4e09-85b1-ff63e2d7a155	9494f712-46cc-4037-ad76-5510fb43332d	1	OA	{DSA,Aptitude}	Medium	1 coding question + MCQs on CS fundamentals.
0654e642-1a36-46a7-bd38-e5ae66e1cb49	9494f712-46cc-4037-ad76-5510fb43332d	2	Technical	{DSA,OOP}	Medium	Focus on clean code and edge cases, not just the correct approach.
0c04e17b-34c4-4507-bd00-232b2a64f80c	9494f712-46cc-4037-ad76-5510fb43332d	3	Technical	{"System Design",DBMS}	Hard	\N
2e40d971-e9ea-4062-a7d5-820791b60f64	9494f712-46cc-4037-ad76-5510fb43332d	4	HR	{Behavioral}	Easy	\N
46a600e4-d155-4677-bfbf-cfbaa387549d	296ba61e-8a64-474e-9051-ba5cbdd1fda8	1	OA	{DSA}	Medium	2 coding questions + a work-style assessment (Leadership Principles).
9d7cc051-11f4-45de-8bce-33dff4433373	296ba61e-8a64-474e-9051-ba5cbdd1fda8	2	Technical	{DSA}	Hard	\N
9bfe0241-9fba-47f4-8e78-add51dff1ed6	296ba61e-8a64-474e-9051-ba5cbdd1fda8	3	Technical	{DSA,"System Design"}	Hard	Every technical round also probes Leadership Principles via 'tell me about a time...' questions.
caf990e3-9bb7-4286-96dc-4f5f3cce21b0	296ba61e-8a64-474e-9051-ba5cbdd1fda8	4	HR	{Behavioral}	Medium	\N
e812debb-35a8-419e-8319-365e6a3853d7	b4914043-13d9-43e4-9833-cc9dbcb4e2c5	1	OA	{Aptitude,DSA}	Easy	NQT: quantitative aptitude, reasoning, verbal, plus basic coding.
8d9b5bc3-1e58-464a-aa5b-20937f298e3e	b4914043-13d9-43e4-9833-cc9dbcb4e2c5	2	Technical	{DSA,DBMS,OOP}	Easy	\N
693bd10a-8d3f-4653-8eff-acee5ce8633e	b4914043-13d9-43e4-9833-cc9dbcb4e2c5	3	HR	{Behavioral}	Easy	\N
6c4bcd37-77dc-44ad-8268-b8a0c6f1bb55	1fca9c60-2faf-459b-a5c6-a7f5831b9024	1	OA	{Aptitude}	Easy	InfyTQ-style aptitude + basic programming.
fe3aebd1-eaf7-4b84-8f28-9e106073f0c5	1fca9c60-2faf-459b-a5c6-a7f5831b9024	2	Technical	{DSA,OOP}	Easy	\N
ae4f86a3-d72a-44ea-b9c3-d2169bf79211	1fca9c60-2faf-459b-a5c6-a7f5831b9024	3	HR	{Behavioral}	Easy	\N
09b4f03d-22ab-47d1-9ed1-1870fee01a58	b3b086e1-364f-464e-9dee-b60d5f179843	1	OA	{DSA}	Medium	\N
2bd821b3-16f4-40eb-a3df-bcc7c96c5c47	b3b086e1-364f-464e-9dee-b60d5f179843	2	Technical	{DSA,"System Design"}	Hard	Strong emphasis on real-world system design given fintech scale.
816db478-2e5b-454b-af70-78cf6eca00ab	b3b086e1-364f-464e-9dee-b60d5f179843	3	HR	{Behavioral}	Medium	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: studenthelp
--

COPY public.users (id, name, email, hashed_password, branch, grad_year, cgpa, role, college_name, target_company_ids, created_at, email_verified, leetcode_username, leetcode_daily_goal, leetcode_total_solved, leetcode_easy_solved, leetcode_medium_solved, leetcode_hard_solved, leetcode_streak, leetcode_last_solved_date, must_change_password, institution_id) FROM stdin;
10f2dfe7-169e-4b07-acdb-4547e13781d5	mahi agrawal	mahiagarwal0509@gmail.com	$2b$12$MJ6b8mLteXSxaf19.lUu3.DlSR/JxE4WMWE.KdWfhDtDuJuofK6.2	CSE	2027	\N	student	\N	{}	2026-08-20 21:35:57.500468	f	\N	1	0	0	0	0	0	\N	f	\N
72b5e054-ac6a-47a1-b257-f3cb351f8d88	mehul agrawal	mahi.agarwal.050904@gmail.com	$2b$12$qVqa3poKlCRebNhPJkTT7ObDTC5JCBpBs8WjFdn38kTlm6OfSj0Z.	\N	\N	\N	admin	\N	{}	2026-08-21 10:05:48.873451	t	\N	1	0	0	0	0	0	\N	t	\N
b6af0dc1-f90d-4548-a542-fb112dce0cfa	mehul agrawal	neha.agrawal.2182@gmail.com	$2b$12$E1oYfMkmqIpM2YikQ55LKOZleND1mQqcXpoWZrzp4dMZSqb.eghnu	\N	\N	\N	admin	\N	{}	2026-08-21 10:12:48.52505	t	\N	1	0	0	0	0	0	\N	t	\N
c52c8617-3724-44f3-af04-aebcbc245ece	mahi	mahiagrawal.821525@gmail.com	$2b$12$6kK2dzJ1Jb6ED4/z8T9iaOAN9BGdckI2dSG81yW1yh1QlZGrvMyom	cse	2027	\N	student	\N	{}	2026-08-31 19:54:28.619564	f	\N	1	0	0	0	0	0	\N	f	\N
0eb7e6cf-918e-4d71-945b-3d9fbe576e86	StudentHelp Admin	admin@studenthelp.dev	$2b$12$A1H9wS3OGLEIDg3Y8K4U0OGstTWJ4qQ0nQopoDTkr3poo/N5iXVZ6	\N	\N	\N	admin	\N	{}	2026-08-21 08:13:58.705532	t	\N	1	0	0	0	0	0	\N	f	\N
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: applications applications_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: institutions institutions_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.institutions
    ADD CONSTRAINT institutions_pkey PRIMARY KEY (id);


--
-- Name: interventions interventions_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.interventions
    ADD CONSTRAINT interventions_pkey PRIMARY KEY (id);


--
-- Name: job_listings job_listings_external_id_key; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.job_listings
    ADD CONSTRAINT job_listings_external_id_key UNIQUE (external_id);


--
-- Name: job_listings job_listings_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.job_listings
    ADD CONSTRAINT job_listings_pkey PRIMARY KEY (id);


--
-- Name: learning_resources learning_resources_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.learning_resources
    ADD CONSTRAINT learning_resources_pkey PRIMARY KEY (id);


--
-- Name: leetcode_logs leetcode_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.leetcode_logs
    ADD CONSTRAINT leetcode_logs_pkey PRIMARY KEY (id);


--
-- Name: mock_interview_sessions mock_interview_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.mock_interview_sessions
    ADD CONSTRAINT mock_interview_sessions_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: prep_plans prep_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.prep_plans
    ADD CONSTRAINT prep_plans_pkey PRIMARY KEY (id);


--
-- Name: qa_answers qa_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_answers
    ADD CONSTRAINT qa_answers_pkey PRIMARY KEY (id);


--
-- Name: qa_questions qa_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_questions
    ADD CONSTRAINT qa_questions_pkey PRIMARY KEY (id);


--
-- Name: qa_upvotes qa_upvotes_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_upvotes
    ADD CONSTRAINT qa_upvotes_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_questions quiz_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_pkey PRIMARY KEY (id);


--
-- Name: quiz_results quiz_results_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.quiz_results
    ADD CONSTRAINT quiz_results_pkey PRIMARY KEY (id);


--
-- Name: readiness_scores readiness_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.readiness_scores
    ADD CONSTRAINT readiness_scores_pkey PRIMARY KEY (id);


--
-- Name: resumes resumes_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_pkey PRIMARY KEY (id);


--
-- Name: roadmaps roadmaps_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.roadmaps
    ADD CONSTRAINT roadmaps_pkey PRIMARY KEY (id);


--
-- Name: rounds rounds_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.rounds
    ADD CONSTRAINT rounds_pkey PRIMARY KEY (id);


--
-- Name: qa_upvotes uq_user_answer_upvote; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_upvotes
    ADD CONSTRAINT uq_user_answer_upvote UNIQUE (user_id, answer_id);


--
-- Name: applications uq_user_company_application; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT uq_user_company_application UNIQUE (user_id, company_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_institution_id; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE INDEX ix_audit_logs_institution_id ON public.audit_logs USING btree (institution_id);


--
-- Name: ix_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE INDEX ix_audit_logs_timestamp ON public.audit_logs USING btree ("timestamp");


--
-- Name: ix_companies_name; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE INDEX ix_companies_name ON public.companies USING btree (name);


--
-- Name: ix_institutions_code; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE UNIQUE INDEX ix_institutions_code ON public.institutions USING btree (code);


--
-- Name: ix_institutions_name; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE UNIQUE INDEX ix_institutions_name ON public.institutions USING btree (name);


--
-- Name: ix_job_listings_company_name; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE INDEX ix_job_listings_company_name ON public.job_listings USING btree (company_name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: studenthelp
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: applications applications_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: applications applications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.applications
    ADD CONSTRAINT applications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(id);


--
-- Name: audit_logs audit_logs_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- Name: chat_messages chat_messages_referenced_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_referenced_company_id_fkey FOREIGN KEY (referenced_company_id) REFERENCES public.companies(id);


--
-- Name: chat_messages chat_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: users fk_users_institution_id; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_institution_id FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- Name: interventions interventions_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.interventions
    ADD CONSTRAINT interventions_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id);


--
-- Name: interventions interventions_institution_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.interventions
    ADD CONSTRAINT interventions_institution_id_fkey FOREIGN KEY (institution_id) REFERENCES public.institutions(id);


--
-- Name: leetcode_logs leetcode_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.leetcode_logs
    ADD CONSTRAINT leetcode_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: mock_interview_sessions mock_interview_sessions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.mock_interview_sessions
    ADD CONSTRAINT mock_interview_sessions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: mock_interview_sessions mock_interview_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.mock_interview_sessions
    ADD CONSTRAINT mock_interview_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: prep_plans prep_plans_target_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.prep_plans
    ADD CONSTRAINT prep_plans_target_company_id_fkey FOREIGN KEY (target_company_id) REFERENCES public.companies(id);


--
-- Name: prep_plans prep_plans_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.prep_plans
    ADD CONSTRAINT prep_plans_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: qa_answers qa_answers_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_answers
    ADD CONSTRAINT qa_answers_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: qa_answers qa_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_answers
    ADD CONSTRAINT qa_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.qa_questions(id);


--
-- Name: qa_questions qa_questions_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_questions
    ADD CONSTRAINT qa_questions_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: qa_questions qa_questions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_questions
    ADD CONSTRAINT qa_questions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: qa_upvotes qa_upvotes_answer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_upvotes
    ADD CONSTRAINT qa_upvotes_answer_id_fkey FOREIGN KEY (answer_id) REFERENCES public.qa_answers(id);


--
-- Name: qa_upvotes qa_upvotes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.qa_upvotes
    ADD CONSTRAINT qa_upvotes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: questions questions_round_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_round_id_fkey FOREIGN KEY (round_id) REFERENCES public.rounds(id);


--
-- Name: quiz_questions quiz_questions_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: quiz_questions quiz_questions_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.quiz_questions
    ADD CONSTRAINT quiz_questions_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES public.users(id);


--
-- Name: quiz_results quiz_results_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.quiz_results
    ADD CONSTRAINT quiz_results_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: readiness_scores readiness_scores_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.readiness_scores
    ADD CONSTRAINT readiness_scores_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: resumes resumes_target_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_target_company_id_fkey FOREIGN KEY (target_company_id) REFERENCES public.companies(id);


--
-- Name: resumes resumes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: roadmaps roadmaps_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.roadmaps
    ADD CONSTRAINT roadmaps_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: rounds rounds_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: studenthelp
--

ALTER TABLE ONLY public.rounds
    ADD CONSTRAINT rounds_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- PostgreSQL database dump complete
--

\unrestrict ur4ExtQt8K5HI1oMaaczPTc6MfhEbTbM7UIgu6WHfZuHIHR1BffGTYYZCgBLxx5

