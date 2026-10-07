# """
# Skill Gap Analyzer - Compares user skills with current job market trends.
# Provides job readiness score, skill gaps, and recommendations.
# """

# from typing import Optional
# from collections import Counter


# # Current job market trends (2024-2026) - Skills in high demand
# JOB_MARKET_TRENDS = {
#     # High demand roles with required skills and weight
#     "Full Stack Developer": {
#         "required": ["JavaScript", "React", "Node.js", "SQL", "Git"],
#         "preferred": ["TypeScript", "Docker", "AWS", "MongoDB", "REST API"],
#         "demand": "Very High",
#         "avg_salary": "$120k - $180k",
#     },
#     "Backend Developer": {
#         "required": ["Python", "SQL", "REST API", "Git"],
#         "preferred": ["Django", "FastAPI", "Docker", "PostgreSQL", "Redis", "Microservices"],
#         "demand": "High",
#         "avg_salary": "$110k - $170k",
#     },
#     "Frontend Developer": {
#         "required": ["JavaScript", "React", "HTML", "CSS", "Git"],
#         "preferred": ["TypeScript", "Next.js", "Tailwind CSS", "Redux", "Testing"],
#         "demand": "High",
#         "avg_salary": "$100k - $160k",
#     },
#     "Data Scientist": {
#         "required": ["Python", "SQL", "Machine Learning", "Statistics"],
#         "preferred": ["TensorFlow", "PyTorch", "Pandas", "Spark", "Deep Learning"],
#         "demand": "Very High",
#         "avg_salary": "$130k - $200k",
#     },
#     "DevOps Engineer": {
#         "required": ["Docker", "Kubernetes", "CI/CD", "Linux", "Git"],
#         "preferred": ["AWS", "Terraform", "Python", "Monitoring", "Security"],
#         "demand": "Very High",
#         "avg_salary": "$130k - $190k",
#     },
#     "Mobile Developer": {
#         "required": ["React Native", "JavaScript", "Mobile Development"],
#         "preferred": ["TypeScript", "iOS", "Android", "Flutter", "REST API"],
#         "demand": "High",
#         "avg_salary": "$115k - $175k",
#     },
#     "Cloud Engineer": {
#         "required": ["AWS", "Cloud", "Linux", "Networking"],
#         "preferred": ["Terraform", "Kubernetes", "Python", "Docker", "Security"],
#         "demand": "Very High",
#         "avg_salary": "$140k - $200k",
#     },
#     "Machine Learning Engineer": {
#         "required": ["Python", "Machine Learning", "TensorFlow", "Deep Learning"],
#         "preferred": ["PyTorch", "MLOps", "Docker", "AWS", "NLP"],
#         "demand": "Extremely High",
#         "avg_salary": "$150k - $220k",
#     },
#     "Cybersecurity Engineer": {
#         "required": ["Security", "Linux", "Networking", "Python"],
#         "preferred": ["Penetration Testing", "SIEM", "Cloud Security", "Cryptography"],
#         "demand": "Very High",
#         "avg_salary": "$130k - $190k",
#     },
#     "Blockchain Developer": {
#         "required": ["Solidity", "Blockchain", "JavaScript", "Smart Contracts"],
#         "preferred": ["Web3", "Ethereum", "React", "Node.js"],
#         "demand": "High",
#         "avg_salary": "$140k - $210k",
#     },
# }

# # Skills with highest market demand (weighted)
# HOT_SKILLS_2024 = {
#     # Skill: (demand_weight, growth_rate)
#     "Python": (95, "High"),
#     "JavaScript": (90, "Stable"),
#     "React": (88, "High"),
#     "AWS": (85, "Very High"),
#     "Docker": (82, "High"),
#     "Kubernetes": (80, "Very High"),
#     "SQL": (78, "Stable"),
#     "TypeScript": (77, "Very High"),
#     "Machine Learning": (85, "Very High"),
#     "Node.js": (75, "Stable"),
#     "Git": (90, "Stable"),
#     "REST API": (75, "Stable"),
#     "PostgreSQL": (70, "Stable"),
#     "MongoDB": (68, "Stable"),
#     "CI/CD": (72, "High"),
#     "Linux": (70, "Stable"),
#     "Terraform": (65, "High"),
#     "Java": (72, "Stable"),
#     "Spring Boot": (65, "Stable"),
#     "Go": (60, "High"),
#     "Rust": (55, "Very High"),
#     "GraphQL": (55, "High"),
#     "Redis": (58, "Stable"),
#     "TensorFlow": (60, "High"),
#     "PyTorch": (62, "Very High"),
#     "Flutter": (55, "High"),
#     "Next.js": (60, "Very High"),
#     "Microservices": (65, "High"),
#     "DevOps": (75, "High"),
#     "Solidity": (50, "High"),
#     "Cybersecurity": (70, "Very High"),
#     "Deep Learning": (65, "Very High"),
#     "NLP": (58, "Very High"),
#     "Data Science": (75, "High"),
# }

# # Skill learning recommendations
# SKILL_LEARNING_PATH = {
#     "Python": {
#         "time": "4-6 weeks",
#         "resources": ["Python.org Tutorial", "Automate the Boring Stuff", "Real Python"],
#         "projects": ["Build a CLI Tool", "Web Scraper", "REST API"],
#     },
#     "JavaScript": {
#         "time": "6-8 weeks",
#         "resources": ["JavaScript.info", "freeCodeCamp", "Eloquent JavaScript"],
#         "projects": ["Todo App", "Weather App", "Portfolio Website"],
#     },
#     "React": {
#         "time": "4-6 weeks",
#         "resources": ["React.dev", "Full Stack Open", "Scrimba"],
#         "projects": ["E-commerce UI", "Dashboard", "Social Media Clone"],
#     },
#     "SQL": {
#         "time": "3-4 weeks",
#         "resources": ["SQLBolt", "Mode SQL Tutorial", "LeetCode SQL"],
#         "projects": ["Database Design", "Analytics Dashboard", "Data Pipeline"],
#     },
#     "Docker": {
#         "time": "2-3 weeks",
#         "resources": ["Docker Docs", "Docker for Beginners", "Play with Docker"],
#         "projects": ["Containerize App", "Docker Compose Setup", "CI/CD Pipeline"],
#     },
#     "AWS": {
#         "time": "6-8 weeks",
#         "resources": ["AWS Free Tier", "Stephane Maarek Course", "A Cloud Guru"],
#         "projects": ["Deploy Web App", "Serverless API", "S3 Static Site"],
#     },
#     "Machine Learning": {
#         "time": "8-12 weeks",
#         "resources": ["Andrew Ng's Course", "Fast.ai", "Kaggle Learn"],
#         "projects": ["Prediction Model", "Image Classifier", "NLP Chatbot"],
#     },
#     "Spring Boot": {
#         "time": "4-6 weeks",
#         "resources": ["Spring.io Guides", "Baeldung", "Amigoscode"],
#         "projects": ["REST API", "E-commerce Backend", "Microservices"],
#     },
#     "Kubernetes": {
#         "time": "4-6 weeks",
#         "resources": ["Kubernetes.io", "KodeKloud", "CKAD Prep"],
#         "projects": ["Deploy Cluster", "Helm Charts", "Service Mesh"],
#     },
#     "TypeScript": {
#         "time": "2-3 weeks",
#         "resources": ["TypeScript Handbook", "Total TypeScript", "Exercism"],
#         "projects": ["Type a JS Project", "React + TS App", "Node.js API"],
#     },
# }

# # Project recommendations based on skills
# PROJECT_RECOMMENDATIONS = {
#     ("Python", "Django"): {
#         "title": "Build an E-Commerce Backend",
#         "tech": "Django & PostgreSQL",
#         "description": "Full-featured e-commerce API with auth, payments, and admin",
#         "difficulty": "Intermediate",
#         "time": "3-4 weeks",
#     },
#     ("Python", "Machine Learning"): {
#         "title": "Develop a Chatbot",
#         "tech": "Python & NLP",
#         "description": "AI chatbot using transformers and intent recognition",
#         "difficulty": "Advanced",
#         "time": "4-6 weeks",
#     },
#     ("JavaScript", "React"): {
#         "title": "Build a Dashboard App",
#         "tech": "React & Chart.js",
#         "description": "Interactive analytics dashboard with real-time data",
#         "difficulty": "Intermediate",
#         "time": "2-3 weeks",
#     },
#     ("Java", "Spring Boot"): {
#         "title": "Build an E-Commerce App",
#         "tech": "Spring Boot & React",
#         "description": "Full-stack e-commerce with microservices architecture",
#         "difficulty": "Advanced",
#         "time": "4-6 weeks",
#     },
#     ("Docker", "Kubernetes"): {
#         "title": "Deploy Microservices",
#         "tech": "K8s & Helm",
#         "description": "Container orchestration with auto-scaling and monitoring",
#         "difficulty": "Advanced",
#         "time": "3-4 weeks",
#     },
#     ("AWS", "Python"): {
#         "title": "Serverless Data Pipeline",
#         "tech": "AWS Lambda & S3",
#         "description": "Event-driven data processing with serverless architecture",
#         "difficulty": "Intermediate",
#         "time": "2-3 weeks",
#     },
#     ("React", "Node.js"): {
#         "title": "Real-time Chat App",
#         "tech": "MERN Stack & Socket.io",
#         "description": "Full-stack chat application with real-time messaging",
#         "difficulty": "Intermediate",
#         "time": "3-4 weeks",
#     },
#     ("Flutter", "Firebase"): {
#         "title": "Social Media App",
#         "tech": "Flutter & Firebase",
#         "description": "Cross-platform social app with auth and real-time features",
#         "difficulty": "Intermediate",
#         "time": "4-5 weeks",
#     },
#     ("Solidity", "Web3"): {
#         "title": "DeFi Protocol",
#         "tech": "Solidity & Hardhat",
#         "description": "Decentralized finance app with smart contracts",
#         "difficulty": "Advanced",
#         "time": "4-6 weeks",
#     },
# }


# def normalize_skill(skill: str) -> str:
#     """Normalize skill name for comparison."""
#     skill_map = {
#         "js": "JavaScript",
#         "ts": "TypeScript",
#         "py": "Python",
#         "node": "Node.js",
#         "nodejs": "Node.js",
#         "react.js": "React",
#         "reactjs": "React",
#         "vue.js": "Vue.js",
#         "postgres": "PostgreSQL",
#         "mysql": "SQL",
#         "ml": "Machine Learning",
#         "ai": "Machine Learning",
#         "k8s": "Kubernetes",
#         "tf": "Terraform",
#         "aws lambda": "AWS",
#         "ec2": "AWS",
#         "s3": "AWS",
#     }
#     skill_lower = skill.lower().strip()
#     return skill_map.get(skill_lower, skill)


# def calculate_job_readiness(user_skills: list[str], target_role: Optional[str] = None) -> dict:
#     """
#     Calculate job readiness score based on user skills vs market requirements.
#     Returns percentage score and breakdown.
#     """
#     if not user_skills:
#         return {
#             "score": 0,
#             "level": "Beginner",
#             "matched_skills": [],
#             "missing_critical": list(HOT_SKILLS_2024.keys())[:5],
#         }
    
#     # Normalize user skills
#     normalized_skills = [normalize_skill(s) for s in user_skills]
#     user_skills_lower = [s.lower() for s in normalized_skills]
    
#     # Calculate against hot skills
#     matched_hot_skills = []
#     total_weight = 0
#     matched_weight = 0
    
#     for skill, (weight, _) in HOT_SKILLS_2024.items():
#         total_weight += weight
#         if skill.lower() in user_skills_lower or any(skill.lower() in us for us in user_skills_lower):
#             matched_hot_skills.append(skill)
#             matched_weight += weight
    
#     # Base score from hot skills
#     hot_skill_score = (matched_weight / total_weight * 100) if total_weight > 0 else 0
    
#     # If target role specified, also check role-specific skills
#     role_score = 0
#     role_matched = []
#     role_missing = []
    
#     if target_role and target_role in JOB_MARKET_TRENDS:
#         role_data = JOB_MARKET_TRENDS[target_role]
#         required = role_data["required"]
#         preferred = role_data.get("preferred", [])
        
#         for skill in required:
#             if skill.lower() in user_skills_lower or any(skill.lower() in us for us in user_skills_lower):
#                 role_matched.append(skill)
#             else:
#                 role_missing.append(skill)
        
#         for skill in preferred:
#             if skill.lower() in user_skills_lower or any(skill.lower() in us for us in user_skills_lower):
#                 role_matched.append(skill)
        
#         # Required skills worth 70%, preferred worth 30%
#         required_score = (len([s for s in role_matched if s in required]) / len(required)) * 70 if required else 0
#         preferred_score = (len([s for s in role_matched if s in preferred]) / len(preferred)) * 30 if preferred else 0
#         role_score = required_score + preferred_score
    
#     # Final score (weighted average if role specified)
#     if target_role:
#         final_score = (hot_skill_score * 0.4) + (role_score * 0.6)
#     else:
#         final_score = hot_skill_score
    
#     # Determine level
#     if final_score >= 75:
#         level = "Job Ready"
#     elif final_score >= 50:
#         level = "Almost Ready"
#     elif final_score >= 25:
#         level = "Learning"
#     else:
#         level = "Beginner"
    
#     # Find missing critical skills
#     missing_critical = []
#     critical_skills = ["Python", "JavaScript", "SQL", "Git", "Docker", "AWS", "React"]
#     for skill in critical_skills:
#         if skill.lower() not in user_skills_lower:
#             missing_critical.append(skill)
    
#     return {
#         "score": round(final_score, 1),
#         "level": level,
#         "matched_skills": list(set(matched_hot_skills + role_matched)),
#         "missing_critical": missing_critical[:5],
#         "role_specific_missing": role_missing[:5] if role_missing else [],
#     }


# def analyze_skill_gaps(user_skills: list[str], target_role: str = None, github_skills: list[str] = None) -> dict:
#     """
#     Comprehensive skill gap analysis comparing user skills with market trends.
#     """
#     # Combine all user skills
#     all_skills = list(set(user_skills + (github_skills or [])))
#     normalized_skills = [normalize_skill(s) for s in all_skills]
#     skills_lower = [s.lower() for s in normalized_skills]
    
#     # If target role is specified, focus analysis on that role
#     target_role_data = None
#     target_role_skills_matched = []
#     target_role_skills_missing = []
#     target_role_match_pct = 0
    
#     if target_role and target_role in JOB_MARKET_TRENDS:
#         target_role_data = JOB_MARKET_TRENDS[target_role]
#         required = target_role_data["required"]
#         preferred = target_role_data.get("preferred", [])
#         all_role_skills = required + preferred
        
#         for skill in all_role_skills:
#             if skill.lower() in skills_lower or any(skill.lower() in us for us in skills_lower):
#                 target_role_skills_matched.append(skill)
#             else:
#                 target_role_skills_missing.append(skill)
        
#         target_role_match_pct = round((len(target_role_skills_matched) / len(all_role_skills)) * 100) if all_role_skills else 0
    
#     # Find best matching roles
#     role_matches = []
#     for role, data in JOB_MARKET_TRENDS.items():
#         required = data["required"]
#         preferred = data.get("preferred", [])
#         all_role_skills = required + preferred
        
#         matched = sum(1 for s in all_role_skills if s.lower() in skills_lower or any(s.lower() in us for us in skills_lower))
#         match_pct = (matched / len(all_role_skills)) * 100 if all_role_skills else 0
        
#         role_matches.append({
#             "role": role,
#             "match_percentage": round(match_pct),
#             "demand": data["demand"],
#             "salary": data["avg_salary"],
#             "matched_skills": [s for s in all_role_skills if s.lower() in skills_lower],
#             "missing_skills": [s for s in all_role_skills if s.lower() not in skills_lower],
#             "required_skills": required,
#             "preferred_skills": preferred,
#         })
    
#     # Sort by match percentage
#     role_matches.sort(key=lambda x: x["match_percentage"], reverse=True)
    
#     # Skills to learn (prioritize target role skills if specified)
#     skills_to_learn = []
    
#     if target_role and target_role_skills_missing:
#         # Prioritize missing skills from target role
#         for skill in target_role_skills_missing:
#             learning_info = SKILL_LEARNING_PATH.get(skill, {})
#             skills_to_learn.append({
#                 "skill": skill,
#                 "priority": "high" if skill in JOB_MARKET_TRENDS.get(target_role, {}).get("required", []) else "medium",
#                 "time_to_learn": learning_info.get("time", "4-6 weeks"),
#                 "resource": learning_info.get("resources", [""])[0] if learning_info.get("resources") else None,
#                 "reason": f"Required for {target_role}",
#             })
#             if len(skills_to_learn) >= 6:
#                 break
    
#     # Add high-demand skills if we haven't filled 6 yet
#     if len(skills_to_learn) < 6:
#         for skill, (weight, growth) in sorted(HOT_SKILLS_2024.items(), key=lambda x: x[1][0], reverse=True):
#             if skill.lower() not in skills_lower and skill not in [s["skill"] for s in skills_to_learn]:
#                 learning_info = SKILL_LEARNING_PATH.get(skill, {})
#                 skills_to_learn.append({
#                     "skill": skill,
#                     "priority": "high" if weight >= 80 else "medium",
#                     "time_to_learn": learning_info.get("time", "4-6 weeks"),
#                     "resource": learning_info.get("resources", [""])[0] if learning_info.get("resources") else None,
#                     "reason": f"High market demand ({growth} growth)",
#                 })
#                 if len(skills_to_learn) >= 6:
#                     break
    
#     # Project recommendations
#     projects = []
#     for (skill1, skill2), project in PROJECT_RECOMMENDATIONS.items():
#         if skill1.lower() in skills_lower or skill2.lower() in skills_lower:
#             projects.append({
#                 "name": project["title"],
#                 "description": project["description"],
#                 "skills": [skill1, skill2],
#                 "difficulty": project.get("difficulty", "Intermediate"),
#             })
#             if len(projects) >= 4:
#                 break
    
#     # If no matching projects, add general recommendations
#     if not projects:
#         projects = [
#             {"name": "Build a Portfolio Website", "description": "Showcase your projects and skills", "skills": ["HTML", "CSS", "JavaScript"], "difficulty": "Beginner"},
#             {"name": "Create a REST API", "description": "Learn backend fundamentals", "skills": ["Python", "Flask"], "difficulty": "Beginner"},
#         ]
    
#     # Calculate overall readiness
#     if target_role:
#         readiness = calculate_job_readiness(all_skills, target_role)
#     else:
#         readiness = calculate_job_readiness(all_skills)
    
#     # Resume tips based on skills
#     resume_tips = []
#     if any(s in skills_lower for s in ["rest", "api", "backend"]):
#         resume_tips.append("Highlight REST API experience with specific endpoints built")
#     if any(s in skills_lower for s in ["python", "javascript", "java"]):
#         resume_tips.append("Add metrics: 'Reduced API response time by 40%'")
#     if any(s in skills_lower for s in ["react", "angular", "vue"]):
#         resume_tips.append("Showcase UI/UX improvements with user impact")
#     resume_tips.append("Use ATS-friendly keywords from job descriptions")
#     resume_tips.append("Include GitHub/portfolio links for each project")
    
#     return {
#         "job_readiness": readiness["score"],
#         "readiness_level": readiness["level"],
#         "matched_skills": readiness["matched_skills"],
#         "missing_skills": readiness.get("missing_critical", []) + readiness.get("role_specific_missing", []),
#         "skills_to_learn": skills_to_learn[:6],
#         "matching_roles": role_matches[:5],
#         "project_recommendations": projects[:4],
#         "resume_tips": resume_tips[:5],
#         "target_role_analysis": {
#             "role": target_role,
#             "match_percentage": target_role_match_pct,
#             "skills_matched": target_role_skills_matched,
#             "skills_missing": target_role_skills_missing,
#             "role_data": target_role_data,
#         } if target_role else None,
#     }


# def get_available_roles() -> list[dict]:
#     """Return all available job roles with their requirements."""
#     roles = []
#     for role, data in JOB_MARKET_TRENDS.items():
#         roles.append({
#             "name": role,
#             "demand": data["demand"],
#             "salary": data["avg_salary"],
#             "required_skills": data["required"],
#             "preferred_skills": data.get("preferred", []),
#         })
#     return roles


# def get_company_job_match(user_skills: list[str], companies: list[str] = None) -> list:
#     """
#     Calculate match percentage for specific companies based on typical tech stacks.
#     Returns a sorted list of company matches.
#     """
#     # Typical tech stacks for major companies (simplified)
#     company_stacks = {
#         "Amazon": ["Java", "Python", "AWS", "Docker", "Microservices", "SQL", "Linux"],
#         "Google": ["Python", "Java", "Go", "Kubernetes", "TensorFlow", "SQL", "C++"],
#         "Microsoft": ["C#", ".NET", "Azure", "TypeScript", "Python", "SQL", "React"],
#         "Meta": ["Python", "React", "GraphQL", "MySQL", "C++", "Machine Learning"],
#         "Netflix": ["Java", "Python", "AWS", "Microservices", "Cassandra", "Kafka"],
#         "Apple": ["Swift", "Objective-C", "Python", "Machine Learning", "iOS"],
#         "Infosys": ["Java", "Spring Boot", "SQL", "Python", "Angular", "AWS"],
#         "TCS": ["Java", "Python", "SQL", "Angular", "React", "AWS", "Azure"],
#         "Wipro": ["Java", "Python", ".NET", "SQL", "Cloud", "DevOps"],
#         "Accenture": ["Java", "Python", "Cloud", "AI", "Salesforce", "SAP"],
#         "IBM": ["Java", "Python", "Cloud", "AI", "Kubernetes", "Linux"],
#         "Cognizant": ["Java", ".NET", "Python", "AWS", "Azure", "DevOps"],
#     }
    
#     if companies:
#         company_stacks = {k: v for k, v in company_stacks.items() if k in companies}
    
#     skills_lower = [s.lower() for s in user_skills]
    
#     matches = []
#     for company, stack in company_stacks.items():
#         matched = sum(1 for s in stack if s.lower() in skills_lower or any(s.lower() in us for us in skills_lower))
#         match_pct = round((matched / len(stack)) * 100) if stack else 0
        
#         matches.append({
#             "company": company,
#             "match": match_pct,
#             "matched_skills": [s for s in stack if s.lower() in skills_lower],
#             "skills_to_add": [s for s in stack if s.lower() not in skills_lower][:3],
#         })
    
#     # Sort by match percentage descending
#     return sorted(matches, key=lambda x: x["match"], reverse=True)








from collections import Counter


def get_required_skills(role: str, jobs_df, top_n: int = 15) -> list:
    role = role.lower().strip()
    rows = jobs_df[
        jobs_df["job_title"].str.contains(role, na=False)
        | jobs_df["category"].str.contains(role, na=False)
    ]
    counter = Counter(s for lst in rows["skills"] for s in lst)
    return [skill for skill, _ in counter.most_common(top_n)]


def skill_gap(user_skills, role, jobs_df, cand_df=None):
    required = get_required_skills(role, jobs_df)
    if not required and cand_df is not None:      # fallback source
        required = required_from_candidates(role, cand_df)
    user = {s.lower().strip() for s in user_skills}
    matched = [s for s in required if s in user]
    missing = [s for s in required if s not in user]
    return {
        "role": role,
        "matched": matched,
        "missing": missing,
        "required": required,
        "match_percent": round(len(matched) / max(len(required), 1) * 100, 1),
    }
    
def required_from_candidates(role: str, cand_df, top_n: int = 10) -> list:
    rows = cand_df[cand_df["job_role"].str.lower() == role.lower().strip()]
    counter = Counter(s for lst in rows["skills"] for s in lst)
    return [s for s, _ in counter.most_common(top_n)]