# Nithin Eswarappa.pdf — five-resume schema pilot

Selection: Three-page research CV; publications mixed with research employment, repeated footer contact, uncertain dates and professional membership without schema slots.

Saved input: `reports/pilot100-additional-llm-20261021-025143/deepseek/documents/a8e2f5e11876fb6c4305.json` → `local_sections`. Pages: [1, 2, 3]. Source blocks: 128. No new extraction/block detection was run. Original PDF was not independently examined for this evaluation.

Recovers research and employment records from locally misclassified publications, keeps awards/membership out of certifications and identifies repeated footer contacts. Education and Siemens date associations remain ambiguous; graduate-student history represented as employment is policy-ambiguous. Two explicit specializations are left null. One quote points to the wrong block for autonomous; one technology citation omits its continuation block. Original source contains interleaved text, not a mapping-created PDF omission.

- Critical-field agreement proxy: **21/21 = 100.0%**.
- Same-block local heuristic baseline on the same critical set: **1/21**.
- Raw field citation contract: **105/107 = 98.13%**.
- Populated-value source-block assessment: {"correct_mapping": 93, "ambiguous": 14, "not_populated": 15, "missing_assignment": 2}.
- Human-verified/PDF-verified accuracy: **not established**.

## Complete mapping output

[Mapping JSON](mapping.json) · [Unmodified provider mapping and citations](mapping-raw.json) · [Full provider envelope/usage](response-envelope.json) · [Saved source blocks](source-blocks.md) · [Every evaluated field](field-evaluation.json)

```json
{
  "contact": {
    "full_name": "NITHIN ESWARAPPA",
    "email": "nithinee@gmail.com",
    "phone": "9916476627",
    "location": "BANGALORE · INDIA",
    "linkedin_url": null,
    "github_url": null,
    "portfolio_url": null
  },
  "professional_title": null,
  "summary": "I have researched and developed solutions for projects involving multimodal vision sensors, optimized for embedded platforms, performing data fusion, object detection, and segmentation. My recent research interests include image synthesis, image translation,, multimodal / multisource image registration and fusion, vision foundation models and 3D perception using vision only sensors.",
  "total_experience_years": 7.0,
  "skills": {
    "technical_skills": [
      "C/C++",
      "Python",
      "Matlab",
      "Bash"
    ],
    "tools_and_platforms": [
      "Git",
      "LaTeX",
      "OpenCV",
      "Robot Operating System (ROS)",
      "QGIS",
      "SNAP Toolbox",
      "QT",
      "Visual Code",
      "Nvidia Jetson Platforms",
      "Arduino",
      "BeagleBone",
      "DM365",
      "DM8168",
      "IMX6",
      "Ubuntu",
      "Windows"
    ],
    "domain_and_functional": [
      "Embedded systems"
    ],
    "soft_skills": [],
    "all_skills": [
      "C/C++",
      "Python",
      "Matlab",
      "Bash",
      "Git",
      "LaTeX",
      "OpenCV",
      "Robot Operating System (ROS)",
      "QGIS",
      "SNAP Toolbox",
      "QT",
      "Visual Code",
      "Nvidia Jetson Platforms",
      "Arduino",
      "BeagleBone",
      "DM365",
      "DM8168",
      "IMX6",
      "Ubuntu",
      "Windows",
      "Embedded systems"
    ]
  },
  "experience": [
    {
      "company": "Multi Sensor Image Fusion Lab (DRDO grant), GITAM University",
      "role": "RESEARCH ASSOCIATE",
      "start_date": "Oct 2023",
      "end_date": "Now",
      "duration": "Oct 2023 - Now",
      "location": "Bengaluru, India",
      "responsibilities": [
        "Research on trimodal image fusion using Visible, Infrared, and SAR images for aiding human operator and multimodal image fusion for object detection and classification."
      ],
      "technologies": []
    },
    {
      "company": "PESIT",
      "role": "GRADUATE STUDENT",
      "start_date": "Oct 2013",
      "end_date": "Apr 2015",
      "duration": "Oct 2013 - Apr 2015",
      "location": "Bangalore, India",
      "responsibilities": [
        "Master’s Thesis: “Appearance based terrain learning and classification for autonomous mobile robot navigation”, advised by Prof Prabhakar Mishra."
      ],
      "technologies": []
    },
    {
      "company": "Vimaan.ai",
      "role": "Senior Firmware Engineer - Robotics",
      "start_date": "Apr 2020",
      "end_date": "Jul 2022",
      "duration": "Apr 2020 - Jul 2022",
      "location": "Bengaluru, India",
      "responsibilities": [
        "Developed a method for absolute localization with 6-DOF, in indoor environments, using camera pose estimation with the use of ArUco markers.",
        "Developed a method for relative pose estimation using stereo data from Intel RealSense depth cameras for drone localization in indoor environments.",
        "Automated recharging of drone batteries using a battery management system for continuous autonomous drone operations."
      ],
      "technologies": [
        "ArUco markers",
        "Intel RealSense depth cameras"
      ]
    },
    {
      "company": "Tonbo Imaging",
      "role": "Member of Technical Staff",
      "start_date": "Apr 2015",
      "end_date": "Jun 2018",
      "duration": "Apr 2015 – Jun 2018",
      "location": "Bengaluru, India",
      "responsibilities": [
        "Conducted research and development of methods, to correct motion blur in narrow FOV images, from dual electro Optronics (thermal IR and visible) on a continuously rotating (360°/sec) multi sensor imaging platform.",
        "Developed methods for stitching 360° panoramic image from line of sight stabilized images for long range passive RADAR, used for surveillance and automatic threat detection from air and sea.",
        "Designed and developed a synchronization (camera sensor – Vsync) mechanism, and optical motor control protocol for motion blur correction on an embedded platform.",
        "Designed and developed Target-pointing (Geo-pointing) capability for Pan Tilt Unit (PTU) mounted imaging systems on embedded platforms, integrating multiple subsystems such as GPS, digital magnetic compass, and ground based RADAR.",
        "Developed algorithms for rolling shutter correction, image blur correction, non uniformity correction, and automatic gain correction for thermal images.",
        "Automated a tool for Optical centre estimation without calibration and field of view estimation for multiple zoom steps.",
        "Developed command control interface for multi-sensor active range gated camera and arranged and conducted meetings with the vendors for technology - knowledge transfer and module integration into systems.",
        "Developed a multi-interface (Serial/UDP/TCP) multithreaded communication architecture on embedded Linux for remote command and control of multi sensor surveillance platforms (Camera TIR, Visible, PTU, GPU, Compass, LRF)."
      ],
      "technologies": [
        "GPS",
        "digital magnetic compass",
        "ground based RADAR",
        "Serial",
        "UDP",
        "TCP",
        "embedded Linux"
      ]
    },
    {
      "company": "Siemens Information Systems Ltd.",
      "role": "Systems Engineer",
      "start_date": "Jul 2008",
      "end_date": "Apr 2009",
      "duration": "Jul 2008 - Apr 2009",
      "location": "Bengaluru, India",
      "responsibilities": [
        "Developed functionalities and addressed change requests in the service module of Syngo – Siemens Health care, Medical Imaging software."
      ],
      "technologies": []
    }
  ],
  "education": [
    {
      "institution": "Visvesvaraya Technological University",
      "degree": "Master Of Technology In Intelligent Systems",
      "field_of_study": null,
      "start_year": null,
      "graduation_year": "December 2015",
      "grade_or_gpa": null
    },
    {
      "institution": "Visvesvaraya Technological University",
      "degree": "Bachelor of Engineering in Electronics and Communication",
      "field_of_study": null,
      "start_year": null,
      "graduation_year": "June 2008",
      "grade_or_gpa": null
    }
  ],
  "certifications": [],
  "projects": [],
  "languages": []
}
```

## Field-by-field results

`correct_mapping` is provisional AI analyst source-block agreement, not independent human truth. `citation_error` can coexist with correct value content. Analyst source references supplement the evaluation; they do not retroactively repair the raw provider response. Null/empty fields are retained for inspection; absence and ambiguity reasons are in the JSON. The CSV/JSON contain full values and exact quote text; the table abbreviates long values.

| Field | LLM value | Mapping assessment | Raw citation assessment | Analyst source IDs |
|---|---|---|---|---|
| `/contact/full_name` | NITHIN ESWARAPPA | correct_mapping | citation_supported | e0:0:16 |
| `/contact/email` | nithinee@gmail.com | ambiguous | citation_supported | e2:0:18 |
| `/contact/phone` | 9916476627 | correct_mapping | citation_supported | e1:0:30 |
| `/contact/location` | BANGALORE · INDIA | correct_mapping | citation_supported | e1:0:30 |
| `/contact/linkedin_url` | None | not_populated | not_populated |  |
| `/contact/github_url` | None | not_populated | not_populated |  |
| `/contact/portfolio_url` | None | not_populated | not_populated |  |
| `/professional_title` | None | not_populated | not_populated |  |
| `/summary` | I have researched and developed solutions for projects involving multimodal vision sensors, optimized for embedded platforms, performing data fusion, object detection, and segmentation. My recent research interests include image synthesis, image tran… | correct_mapping | citation_supported | e6:0:106, e6:106:205, e6:205:316, e6:316:392 |
| `/total_experience_years` | 7.0 | correct_mapping | citation_supported | e6:402:413 |
| `/skills/technical_skills/0` | C/C++ | correct_mapping | citation_supported | e69:0:52 |
| `/skills/technical_skills/1` | Python | correct_mapping | citation_supported | e69:0:52 |
| `/skills/technical_skills/2` | Matlab | correct_mapping | citation_supported | e69:0:52 |
| `/skills/technical_skills/3` | Bash | correct_mapping | citation_supported | e69:0:52 |
| `/skills/tools_and_platforms/0` | Git | correct_mapping | citation_supported | e28:0:80 |
| `/skills/tools_and_platforms/1` | LaTeX | correct_mapping | citation_supported | e69:0:52 |
| `/skills/tools_and_platforms/2` | OpenCV | correct_mapping | citation_supported | e69:55:109 |
| `/skills/tools_and_platforms/3` | Robot Operating System (ROS) | correct_mapping | citation_supported | e69:55:109 |
| `/skills/tools_and_platforms/4` | QGIS | correct_mapping | citation_supported | e69:112:160 |
| `/skills/tools_and_platforms/5` | SNAP Toolbox | correct_mapping | citation_supported | e69:112:160 |
| `/skills/tools_and_platforms/6` | QT | correct_mapping | citation_supported | e69:112:160 |
| `/skills/tools_and_platforms/7` | Visual Code | correct_mapping | citation_supported | e69:112:160 |
| `/skills/tools_and_platforms/8` | Nvidia Jetson Platforms | correct_mapping | citation_supported | e69:163:246 |
| `/skills/tools_and_platforms/9` | Arduino | correct_mapping | citation_supported | e69:163:246 |
| `/skills/tools_and_platforms/10` | BeagleBone | correct_mapping | citation_supported | e69:163:246 |
| `/skills/tools_and_platforms/11` | DM365 | correct_mapping | citation_supported | e69:163:246 |
| `/skills/tools_and_platforms/12` | DM8168 | correct_mapping | citation_supported | e69:163:246 |
| `/skills/tools_and_platforms/13` | IMX6 | correct_mapping | citation_supported | e69:163:246 |
| `/skills/tools_and_platforms/14` | Ubuntu | correct_mapping | citation_supported | e69:249:282 |
| `/skills/tools_and_platforms/15` | Windows | correct_mapping | citation_supported | e69:249:282 |
| `/skills/domain_and_functional/0` | Embedded systems | correct_mapping | citation_supported | e69:163:246 |
| `/skills/soft_skills` | [] | not_populated | not_populated |  |
| `/skills/all_skills/0` | C/C++ | correct_mapping | citation_supported | e69:0:52 |
| `/skills/all_skills/1` | Python | correct_mapping | citation_supported | e69:0:52 |
| `/skills/all_skills/2` | Matlab | correct_mapping | citation_supported | e69:0:52 |
| `/skills/all_skills/3` | Bash | correct_mapping | citation_supported | e69:0:52 |
| `/skills/all_skills/4` | Git | correct_mapping | citation_supported | e28:0:80 |
| `/skills/all_skills/5` | LaTeX | correct_mapping | citation_supported | e69:0:52 |
| `/skills/all_skills/6` | OpenCV | correct_mapping | citation_supported | e69:55:109 |
| `/skills/all_skills/7` | Robot Operating System (ROS) | correct_mapping | citation_supported | e69:55:109 |
| `/skills/all_skills/8` | QGIS | correct_mapping | citation_supported | e69:112:160 |
| `/skills/all_skills/9` | SNAP Toolbox | correct_mapping | citation_supported | e69:112:160 |
| `/skills/all_skills/10` | QT | correct_mapping | citation_supported | e69:112:160 |
| `/skills/all_skills/11` | Visual Code | correct_mapping | citation_supported | e69:112:160 |
| `/skills/all_skills/12` | Nvidia Jetson Platforms | correct_mapping | citation_supported | e69:163:246 |
| `/skills/all_skills/13` | Arduino | correct_mapping | citation_supported | e69:163:246 |
| `/skills/all_skills/14` | BeagleBone | correct_mapping | citation_supported | e69:163:246 |
| `/skills/all_skills/15` | DM365 | correct_mapping | citation_supported | e69:163:246 |
| `/skills/all_skills/16` | DM8168 | correct_mapping | citation_supported | e69:163:246 |
| `/skills/all_skills/17` | IMX6 | correct_mapping | citation_supported | e69:163:246 |
| `/skills/all_skills/18` | Ubuntu | correct_mapping | citation_supported | e69:249:282 |
| `/skills/all_skills/19` | Windows | correct_mapping | citation_supported | e69:249:282 |
| `/skills/all_skills/20` | Embedded systems | correct_mapping | citation_supported | e69:163:246 |
| `/experience/0/company` | Multi Sensor Image Fusion Lab (DRDO grant), GITAM University | correct_mapping | citation_supported | e28:0:80 |
| `/experience/0/role` | RESEARCH ASSOCIATE | correct_mapping | citation_supported | e28:0:80 |
| `/experience/0/start_date` | Oct 2023 | correct_mapping | citation_supported | e29:0:14 |
| `/experience/0/end_date` | Now | correct_mapping | citation_supported | e29:0:14 |
| `/experience/0/duration` | Oct 2023 - Now | correct_mapping | citation_supported | e29:0:14 |
| `/experience/0/location` | Bengaluru, India | correct_mapping | citation_supported | e9:14:30 |
| `/experience/0/responsibilities/0` | Research on trimodal image fusion using Visible, Infrared, and SAR images for aiding human operator and multimodal image fusion for object detection and classification. | correct_mapping | citation_supported | e28:83:167, e30:0:100 |
| `/experience/0/technologies` | [] | not_populated | not_populated |  |
| `/experience/1/company` | PESIT | ambiguous | citation_supported | e34:0:55 |
| `/experience/1/role` | GRADUATE STUDENT | ambiguous | citation_supported | e34:0:55 |
| `/experience/1/start_date` | Oct 2013 | ambiguous | citation_supported | e34:58:163 |
| `/experience/1/end_date` | Apr 2015 | ambiguous | citation_supported | e34:58:163 |
| `/experience/1/duration` | Oct 2013 - Apr 2015 | ambiguous | citation_supported | e34:58:163 |
| `/experience/1/location` | Bangalore, India | ambiguous | citation_supported | e35:0:76 |
| `/experience/1/responsibilities/0` | Master’s Thesis: “Appearance based terrain learning and classification for autonomous mobile robot navigation”, advised by Prof Prabhakar Mishra. | ambiguous | not_literal_in_source | e34:58:163, e34:58:163, e35:0:76 |
| `/experience/1/technologies` | [] | not_populated | not_populated |  |
| `/experience/2/company` | Vimaan.ai | correct_mapping | citation_supported | e48:0:46 |
| `/experience/2/role` | Senior Firmware Engineer - Robotics | correct_mapping | citation_supported | e48:0:46 |
| `/experience/2/start_date` | Apr 2020 | correct_mapping | citation_supported | e49:0:21 |
| `/experience/2/end_date` | Jul 2022 | correct_mapping | citation_supported | e49:0:21 |
| `/experience/2/duration` | Apr 2020 - Jul 2022 | correct_mapping | citation_supported | e49:0:21 |
| `/experience/2/location` | Bengaluru, India | correct_mapping | citation_supported | e9:14:30 |
| `/experience/2/responsibilities/0` | Developed a method for absolute localization with 6-DOF, in indoor environments, using camera pose estimation with the use of ArUco markers. | correct_mapping | citation_supported | e50:0:99, e50:99:140 |
| `/experience/2/responsibilities/1` | Developed a method for relative pose estimation using stereo data from Intel RealSense depth cameras for drone localization in indoor environments. | correct_mapping | citation_supported | e51:0:101, e51:101:147 |
| `/experience/2/responsibilities/2` | Automated recharging of drone batteries using a battery management system for continuous autonomous drone operations. | correct_mapping | citation_supported | e52:0:89, e52:89:117 |
| `/experience/2/technologies/0` | ArUco markers | correct_mapping | citation_supported | e50:99:140 |
| `/experience/2/technologies/1` | Intel RealSense depth cameras | correct_mapping | citation_supported | e51:0:101 |
| `/experience/3/company` | Tonbo Imaging | correct_mapping | citation_supported | e53:0:40 |
| `/experience/3/role` | Member of Technical Staff | correct_mapping | citation_supported | e53:0:40 |
| `/experience/3/start_date` | Apr 2015 | correct_mapping | citation_supported | e34:58:163 |
| `/experience/3/end_date` | Jun 2018 | correct_mapping | citation_supported | e54:0:21 |
| `/experience/3/duration` | Apr 2015 – Jun 2018 | correct_mapping | citation_supported | e54:0:21 |
| `/experience/3/location` | Bengaluru, India | correct_mapping | citation_supported | e9:14:30 |
| `/experience/3/responsibilities/0` | Conducted research and development of methods, to correct motion blur in narrow FOV images, from dual electro Optronics (thermal IR and visible) on a continuously rotating (360°/sec) multi sensor imaging platform. | correct_mapping | citation_supported | e55:0:97, e55:97:204, e55:204:213 |
| `/experience/3/responsibilities/1` | Developed methods for stitching 360° panoramic image from line of sight stabilized images for long range passive RADAR, used for surveillance and automatic threat detection from air and sea. | correct_mapping | citation_supported | e56:0:105, e56:105:190 |
| `/experience/3/responsibilities/2` | Designed and developed a synchronization (camera sensor – Vsync) mechanism, and optical motor control protocol for motion blur correction on an embedded platform. | correct_mapping | citation_supported | e60:2:95, e61:0:68 |
| `/experience/3/responsibilities/3` | Designed and developed Target-pointing (Geo-pointing) capability for Pan Tilt Unit (PTU) mounted imaging systems on embedded platforms, integrating multiple subsystems such as GPS, digital magnetic compass, and ground based RADAR. | correct_mapping | citation_supported | e62:0:97, e62:97:198, e62:198:230 |
| `/experience/3/responsibilities/4` | Developed algorithms for rolling shutter correction, image blur correction, non uniformity correction, and automatic gain correction for thermal images. | correct_mapping | citation_supported | e63:0:107, e63:107:152 |
| `/experience/3/responsibilities/5` | Automated a tool for Optical centre estimation without calibration and field of view estimation for multiple zoom steps. | correct_mapping | citation_supported | e64:0:100, e64:100:120 |
| `/experience/3/responsibilities/6` | Developed command control interface for multi-sensor active range gated camera and arranged and conducted meetings with the vendors for technology - knowledge transfer and module integration into systems. | correct_mapping | citation_supported | e65:0:96, e65:96:196, e65:196:204 |
| `/experience/3/responsibilities/7` | Developed a multi-interface (Serial/UDP/TCP) multithreaded communication architecture on embedded Linux for remote command and control of multi sensor surveillance platforms (Camera TIR, Visible, PTU, GPU, Compass, LRF). | correct_mapping | citation_supported | e66:0:98, e66:98:201, e66:201:242 |
| `/experience/3/technologies/0` | GPS | correct_mapping | citation_supported | e62:97:198 |
| `/experience/3/technologies/1` | digital magnetic compass | correct_mapping | citation_error | e62:97:198, e62:198:230 |
| `/experience/3/technologies/2` | ground based RADAR | correct_mapping | citation_supported | e62:198:230 |
| `/experience/3/technologies/3` | Serial | correct_mapping | citation_supported | e66:0:98 |
| `/experience/3/technologies/4` | UDP | correct_mapping | citation_supported | e66:0:98 |
| `/experience/3/technologies/5` | TCP | correct_mapping | citation_supported | e66:0:98 |
| `/experience/3/technologies/6` | embedded Linux | correct_mapping | citation_supported | e66:0:98, e66:98:201 |
| `/experience/4/company` | Siemens Information Systems Ltd. | correct_mapping | citation_supported | e67:0:50 |
| `/experience/4/role` | Systems Engineer | correct_mapping | citation_supported | e67:0:50 |
| `/experience/4/start_date` | Jul 2008 | ambiguous | citation_supported | e66:201:242 |
| `/experience/4/end_date` | Apr 2009 | ambiguous | citation_supported | e66:201:242 |
| `/experience/4/duration` | Jul 2008 - Apr 2009 | ambiguous | citation_supported | e66:201:242 |
| `/experience/4/location` | Bengaluru, India | ambiguous | citation_supported | e9:14:30 |
| `/experience/4/responsibilities/0` | Developed functionalities and addressed change requests in the service module of Syngo – Siemens Health care, Medical Imaging software. | correct_mapping | citation_supported | e68:0:104, e68:104:136 |
| `/experience/4/technologies` | [] | not_populated | not_populated |  |
| `/education/0/institution` | Visvesvaraya Technological University | correct_mapping | citation_supported | e8:0:38 |
| `/education/0/degree` | Master Of Technology In Intelligent Systems | correct_mapping | citation_supported | e8:38:82 |
| `/education/0/field_of_study` | None | missing_assignment | not_populated | e8:38:82 |
| `/education/0/start_year` | None | not_populated | not_populated |  |
| `/education/0/graduation_year` | December 2015 | ambiguous | citation_supported | e9:0:14 |
| `/education/0/grade_or_gpa` | None | not_populated | not_populated |  |
| `/education/1/institution` | Visvesvaraya Technological University | correct_mapping | citation_supported | e8:0:38 |
| `/education/1/degree` | Bachelor of Engineering in Electronics and Communication | correct_mapping | citation_supported | e8:120:176 |
| `/education/1/field_of_study` | None | missing_assignment | not_populated | e8:120:176 |
| `/education/1/start_year` | None | not_populated | not_populated |  |
| `/education/1/graduation_year` | June 2008 | ambiguous | citation_supported | e10:0:10 |
| `/education/1/grade_or_gpa` | None | not_populated | not_populated |  |
| `/certifications` | [] | not_populated | not_populated |  |
| `/projects` | [] | not_populated | not_populated |  |
| `/languages` | [] | not_populated | not_populated |  |

## Predeclared critical opportunities

Degree plus field_of_study may satisfy one reference degree opportunity. Original month-year strings are accepted when the expected year matches; this does not remove date-association ambiguity. Country codes, punctuation/whitespace, labels such as CGPA and enclosing lab/organization context are normalized as documented in the main report.

| Reference | Target | Expected source fact | Actual value | Result |
|---|---|---|---|---|
| f093 | root.contact.full_name | NITHIN ESWARAPPA | NITHIN ESWARAPPA | correct_mapping |
| f094 | root.contact.phone | 9916476627 | 9916476627 | correct_mapping |
| f095 | root.total_experience_years | 7 | 7.0 | correct_mapping |
| f096 | experience.company | GITAM University | Multi Sensor Image Fusion Lab (DRDO grant), GITAM University | correct_mapping |
| f097 | experience.role | RESEARCH ASSOCIATE | RESEARCH ASSOCIATE | correct_mapping |
| f098 | experience.start_date | Oct 2023 | Oct 2023 | correct_mapping |
| f099 | experience.end_date | Now | Now | correct_mapping |
| f100 | experience.company | Vimaan.ai | Vimaan.ai | correct_mapping |
| f101 | experience.role | Senior Firmware Engineer - Robotics | Senior Firmware Engineer - Robotics | correct_mapping |
| f102 | experience.start_date | Apr 2020 | Apr 2020 | correct_mapping |
| f103 | experience.end_date | Jul 2022 | Jul 2022 | correct_mapping |
| f104 | experience.company | Tonbo Imaging | Tonbo Imaging | correct_mapping |
| f105 | experience.role | Member of Technical Staff | Member of Technical Staff | correct_mapping |
| f106 | experience.start_date | Apr 2015 | Apr 2015 | correct_mapping |
| f107 | experience.end_date | Jun 2018 | Jun 2018 | correct_mapping |
| f108 | experience.company | Siemens Information Systems Ltd. | Siemens Information Systems Ltd. | correct_mapping |
| f109 | experience.role | Systems Engineer | Systems Engineer | correct_mapping |
| f110 | education.degree | Master Of Technology In Intelligent Systems | Master Of Technology In Intelligent Systems | correct_mapping |
| f111 | education.institution | Visvesvaraya Technological University | Visvesvaraya Technological University | correct_mapping |
| f112 | education.degree | Bachelor of Engineering in Electronics and Communication | Bachelor of Engineering in Electronics and Communication | correct_mapping |
| f113 | education.institution | Visvesvaraya Technological University | Visvesvaraya Technological University | correct_mapping |

## Provider missing-information statements

These are provider claims, not independent truth. Compare with field-evaluation.json for analyst disagreements and actual mapping omissions.

```json
[
  {
    "path": "/professional_title",
    "reason": "not_in_source",
    "detail": "No professional headline or specialization label is stated in the source blocks.",
    "source_ids": []
  },
  {
    "path": "/contact/linkedin_url",
    "reason": "not_in_source",
    "detail": "No LinkedIn URL appears in the source.",
    "source_ids": []
  },
  {
    "path": "/contact/github_url",
    "reason": "not_in_source",
    "detail": "No GitHub URL appears in the source.",
    "source_ids": []
  },
  {
    "path": "/contact/portfolio_url",
    "reason": "not_in_source",
    "detail": "No portfolio or personal website URL appears in the source.",
    "source_ids": []
  },
  {
    "path": "/certifications",
    "reason": "not_in_source",
    "detail": "No certifications or licenses are stated; the GATE Fellowship appears under AWARDS and is preserved in upstream_observations rather than presented as a certification.",
    "source_ids": []
  },
  {
    "path": "/languages",
    "reason": "not_in_source",
    "detail": "No spoken languages are stated; document language does not imply spoken English.",
    "source_ids": []
  },
  {
    "path": "/projects",
    "reason": "not_in_source",
    "detail": "No discrete project entries with names are provided; project/thesis content appears under research and mentoring sections.",
    "source_ids": []
  },
  {
    "path": "/total_experience_years",
    "reason": "ambiguous_source",
    "detail": "Source states 'Total Experience: 7+ years.'; the + qualification is preserved rather than resolving to an exact figure.",
    "source_ids": [
      "e6:402:413"
    ]
  },
  {
    "path": "/education/0/start_year",
    "reason": "not_in_source",
    "detail": "Only a completion date 'December 2015' is present for the Master's degree; no start year is given.",
    "source_ids": [
      "e9:0:14"
    ]
  },
  {
    "path": "/education/1/start_year",
    "reason": "not_in_source",
    "detail": "Only a completion date 'June 2008' is present for the Bachelor's degree; no start year is given.",
    "source_ids": [
      "e10:0:10"
    ]
  },
  {
    "path": "/education/*/field_of_study",
    "reason": "ambiguous_source",
    "detail": "Field of study is embedded in the degree text ('Intelligent Systems', 'Electronics and Communication'); not separated in source, so left null rather than inferred.",
    "source_ids": [
      "e8:38:82",
      "e8:120:176"
    ]
  },
  {
    "path": "/education/*/grade_or_gpa",
    "reason": "not_in_source",
    "detail": "No GPA, grade, or honors are stated for either degree.",
    "source_ids": []
  },
  {
    "path": "/education dates (December 2015, June 2008)",
    "reason": "upstream_defect",
    "detail": "Degree rows and date/location rows are separate blocks (e8, e9, e10); association of each date to a specific degree is by order only and should be verified.",
    "source_ids": [
      "e8:38:82",
      "e8:120:176",
      "e9:0:14",
      "e10:0:10"
    ]
  },
  {
    "path": "/experience/0 (Research Associate) end_date/appointment",
    "reason": "ambiguous_source",
    "detail": "Date text is 'Oct 2023 - Now' and another block reads 'BOct 2023 - Nowengaluru, India'; current status inferred from 'Now'.",
    "source_ids": [
      "e29:0:14",
      "e42:0:30"
    ]
  },
  {
    "path": "/experience/1 (Graduate Student) classification",
    "reason": "ambiguous_source",
    "detail": "GRADUATE STUDENT at PESIT with a Master's Thesis and Oct 2013 - Apr 2015 is graduate-student history; represented as work only as presented, not as verified employment.",
    "source_ids": [
      "e34:0:55",
      "e34:58:163"
    ]
  },
  {
    "path": "/experience/4 (Siemens) date association",
    "reason": "upstream_defect",
    "detail": "The date 'Jul 2008 - Apr 2009, Bengaluru, India' appears at the end of the Tonbo bullet block (e66) before the Siemens row (e67); association to Siemens is by order and should be verified.",
    "source_ids": [
      "e66:201:242",
      "e66:242:258",
      "e67:0:50"
    ]
  },
  {
    "path": "/experience/3 (Tonbo) start date",
    "reason": "ambiguous_source",
    "detail": "Tonbo dates 'Apr 2015 – Jun 2018' overlap with graduate-student period 'Oct 2013 - Apr 2015'; not reconciled in source.",
    "source_ids": [
      "e54:0:21",
      "e34:58:163"
    ]
  },
  {
    "path": "/skills classification",
    "reason": "schema_limitation",
    "detail": "Source groups are label-based (Programming, Lib/Middleware, Other Tools, Embedded systems, Operating System); categories were re-mapped and 'Embedded systems' placed under domain while its items are under tools; not verbatim bucket names.",
    "source_ids": [
      "e69:0:52",
      "e69:55:109",
      "e69:112:160",
      "e69:163:246",
      "e69:249:282"
    ]
  },
  {
    "path": "publications (6 IEEE/submission records)",
    "reason": "schema_limitation",
    "detail": "Publications have no dedicated schema field and are preserved in upstream_observations.",
    "source_ids": [
      "e12:0:92",
      "e16:0:91",
      "e19:0:86",
      "e21:0:100",
      "e23:0:99",
      "e25:0:90"
    ]
  },
  {
    "path": "awards (GATE Fellowship) and professional membership (IEEE)",
    "reason": "schema_limitation",
    "detail": "AWARDS and PROFESSIONAL MEMBERSHIP sections have no schema slot; preserved in upstream_observations.",
    "source_ids": [
      "e40:0:60",
      "e37:0:62"
    ]
  },
  {
    "path": "mentoring experience",
    "reason": "schema_limitation",
    "detail": "MENTORING EXPERIENCE content (supervising junior researcher, 10 students, thesis/UG project topics) has no dedicated schema slot; partially unrepresented.",
    "source_ids": [
      "e43:63:164",
      "e45:0:98",
      "e46:0:73"
    ]
  }
]
```

## Provider upstream observations

```json
[
  "Local categories are unreliable: research experience, graduate-student history, awards, mentoring, and publications blocks are labeled 'publications' or 'awards'; reclassified by source text and order.",
  "Introduction text contains a typo 'image translation,,' (double comma) and is preserved verbatim in summary.",
  "Publication records span multiple blocks with interleaved fragments ('Planned', 'Submission', 'Oral', 'preprint', 'George K.') that appear to be status/journal annotations split mid-record; titles include 'BiFIS', 'TriFIS', 'HyLapDFN', 'Conventional vs Deep-Learning Methods for Visible and Infrared Image Fusion: A Comparison', and 'Trimodal Image Fusion Framework for a Visible-Infrared-SAR Benchmark Dataset'.",
  "PROFESSIONAL MEMBERSHIP: 'Member, IEEE (Institute of Electrical & Electronics Engineers)', 'Since 2024' — preserved, no schema slot.",
  "AWARDS: 'GATE Fellowship, Electronics and Communication Engineering, Indian Institute of Technology, Madras, Graduate Aptitude Test in Engineering, Ministry of Human Resource Development (MHRD), Government of India (GOI).' with a detached 'March 2011' — preserved; not treated as a certification.",
  "Block e42 text 'BOct 2023 - Nowengaluru, India' appears garbled/interleaved, likely a merged date and Bangalore location from the research associate entry duplicated in a later section.",
  "Block e68 concatenates the Siemens responsibility with the 'TECHNICAL SKILLS' heading, indicating a segmentation defect between experience and skills sections.",
  "Mentoring section lists topics (Master's Thesis multi-modal image registration; undergraduate projects on disparity estimation, deep-learning visible/thermal fusion, image fusion optimization on Nvidia Jetson); projects list left empty to avoid presenting these as discrete projects.",
  "Two profile handles 'nithineeswar' and 'nithineswarappa' appear near contact details presumably social handles but are unlabeled; not mapped to URLs.",
  "Contact includes two emails: 'nithinee@gmail.com' (personal_information) and 'nithin.eswarappa@gmail.com' (repeated in footers); primary mapped to the personal_information block.",
  "Footer blocks repeating name, email, and page numbers appear on pages 1-3; not counted as source facts."
]
```
