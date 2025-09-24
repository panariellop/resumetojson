# Instructions
Extract information from the provided resume and return it as valid JSON following this exact schema:

{
  "name": "string",
  "education": [
    {
      "institution": "string",
      "date_from": "YYYY-MM-DD",
      "date_to": "YYYY-MM-DD",
      "gpa": "string",
      "relevant_classes": ["string"]
    }
  ],
  "work_experience": [
    {
      "title": "string",
      "location": "string",
      "organization": "string",
      "date_from": "YYYY-MM-DD",
      "date_to": "YYYY-MM-DD",
      "skills": ["string"],
      "description": "string"
    }
  ],
  "other_experience": [
    {
      "title": "string",
      "location": "string",
      "organization": "string"
      "date_from": "YYYY-MM-DD",
      "date_to": "YYYY-MM-DD",
      "skills": [ "string" ],
      "description": "string"
    }
  ],
  "skills": ["string"],
  "references": [
    {
      "name": "string",
      "organization": "string",
      "email": "string",
      "phone_number": "string"
    }
  ]
}

Instructions:
1. Extract all information exactly as presented in the resume
2. For dates:
   - Use ISO format YYYY-MM-DD
   - If only month/year provided, use first day of month (e.g., "May 2023" → "2023-05-01")
   - If only year provided, use January 1st (e.g., "2023" → "2023-01-01")
   - For current/ongoing positions, use today's date for date_to
   - If dates are missing, use null

3. For work_experience:
   - Extract technical and soft skills mentioned in each role into the skills array
   - Combine all bullet points and responsibilities into the description field

4. For other_experience:
   - Include volunteer work, projects, leadership roles, extracurricular activities
   - Do not duplicate items already in work_experience

5. For skills:
   - Compile a comprehensive list of all unique skills mentioned throughout the resume
   - Include technical skills, programming languages, tools, and soft skills

6. For education:
   - Include degrees, certifications, and relevant training programs
   - Extract GPA exactly as written (e.g., "3.85/4.0" or "3.85")
   - List relevant coursework in relevant_classes array

7. For references:
   - Only include if explicitly stated in the resume
   - If references are "available upon request", return empty array []

8. Return ONLY valid JSON with no additional text or explanation
9. Use null for missing optional fields, empty arrays [] for lists with no items
10. Preserve original capitalization and formatting for names and titles

Example: 
```json
{
  "name": "Sarah Chen",
  "education": [
    {
      "institution": "University of California, Berkeley",
      "location": "Berkeley, CA, USA",
      "date_from": "2018-08-15",
      "date_to": "2022-05-15",
      "gpa": "3.78/4.0",
      "relevant_classes": [
        "Data Structures",
        "Algorithms",
        "Machine Learning",
        "Database Systems",
        "Software Engineering"
      ]
    }
  ],
  "work_experience": [
    {
      "title": "Software Engineer II",
      "organization": "TechCorp Inc.",
      "location": "Berkeley, CA, USA",
      "date_from": "2023-06-01",
      "date_to": "2024-12-15",
      "skills": [
        "Python",
        "React",
        "Node.js",
        "AWS",
        "PostgreSQL",
        "Docker",
        "CI/CD",
        "Agile"
      ],
      "description": "Developed and maintained microservices architecture serving 2M+ daily users. Led migration of legacy monolithic application to cloud-native architecture, reducing infrastructure costs by 35%. Implemented automated testing pipeline that improved code coverage from 45% to 87%. Mentored 3 junior developers and conducted code reviews."
    },
    {
      "title": "Junior Software Engineer",
      "organization": "StartupXYZ",
      "location": "Berkeley, CA, USA",
      "date_from": "2022-07-01",
      "date_to": "2023-05-31",
      "skills": [
        "JavaScript",
        "TypeScript",
        "React",
        "MongoDB",
        "Express.js",
        "Git"
      ],
      "description": "Built full-stack web applications using MERN stack. Developed RESTful APIs handling 10,000+ requests per minute. Collaborated with UX team to implement responsive designs. Participated in daily standups and sprint planning sessions."
    },
    {
      "title": "Software Engineering Intern",
      "organization": "Google",
      "location": "Berkeley, CA, USA",
      "date_from": "2021-06-01",
      "date_to": "2021-08-31",
      "skills": [
        "Java",
        "Android",
        "Kotlin",
        "Firebase"
      ],
      "description": "Worked on Android application features for Google Maps. Implemented new accessibility features improving app usability for visually impaired users. Fixed 15+ bugs and improved app performance by 20%."
    }
  ],
  "other_experience": [
    {
      "title": "Open Source Contributor - React Native",
      "organization": null, 
      "location": "Berkeley, CA, USA",
      "date_from": "2022-01-01",
      "date_to": "2024-12-15",
      "description": "Contributing to React Native core library with 5 merged PRs. Focus on performance optimizations and bug fixes."
    },
    {
      "title": "Hackathon Winner - Berkeley Hack 2021",
      "organization": null, 
      "location": "Berkeley, CA, USA",
      "date_from": "2021-10-15",
      "date_to": "2021-10-17",
      "description": "Led team of 4 to develop AI-powered study assistant app. Won first place out of 120 teams."
    },
    {
      "title": "Teaching Assistant - CS61B Data Structures",
      "organization": "UC Berkeley", 
      "location": "Berkeley, CA, USA",
      "date_from": "2021-01-15",
      "date_to": "2021-05-15",
      "description": "Taught weekly lab sections for 30 students. Held office hours and graded assignments. Received 4.8/5.0 teaching rating."
    }
  ],
  "skills": [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "React",
    "Node.js",
    "Express.js",
    "Django",
    "PostgreSQL",
    "MongoDB",
    "AWS",
    "Docker",
    "Kubernetes",
    "Git",
    "CI/CD",
    "Machine Learning",
    "TensorFlow",
    "Agile",
    "Scrum",
    "REST APIs",
    "GraphQL"
  ],
  "references": [
    {
      "name": "Michael Torres",
      "organization": "TechCorp Inc.",
      "email": "mtorres@techcorp.com",
      "phone_number": "+1-415-555-0123"
    },
    {
      "name": "Dr. Lisa Wang",
      "organization": "UC Berkeley",
      "email": "lwang@berkeley.edu",
      "phone_number": "+1-510-555-0456"
    }
  ]
}
 
```

