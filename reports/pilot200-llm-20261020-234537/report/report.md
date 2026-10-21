# 200-document pipeline and DeepSeek review report

**This is an automated development/diagnostic batch, not an accuracy certification.** No independent human-approved reference labels were used. The known pilot relationship defects remain relevant.

## Batch result

Selected **200 documents with 200 distinct SHA256 hashes** from `/mnt/c/Users/Gopi Gedar/Eragina Digital Solutions Private Limited/Eragina Digital - Documents/RESUMES/resume/RESUMES_FLAT`. Selection: original15 +185 additional PDFs, seed42, round-robin page/layout/coverage strata from the previously processed source pool. Java is deliberately retained as known out-of-scope evidence; this is not a claim that all selected documents are genuine candidate resumes. This sample is not an unbiased corpus accuracy estimate.

Local completion: **200/200**. Provider attempted: **200/200**. Structurally valid provider reviews: **196/200**. Failed documents: **4**. Skipped: **0**.

All-local-before-review sequencing: **True**. Local completion `2026-10-21T06:51:13.455883+00:00`; review start `2026-10-21T06:51:13.459537+00:00`. Times are UTC evidence. The preflight credential/model GET sends no resume and is not a review request.

### Review statuses

- llm_reviewed_all_assigned: **180**
- llm_reviewed_needs_review: **9**
- llm_reviewed_no_sections: **1**
- llm_reviewed_out_of_scope: **6**
- review_failed: **4**

Classification requests: **227**. Actual input **6,515,996** + output **199,190** = **6,715,186 tokens**. Multi-call documents: 27; recorded invalid-response attempts: 19; failed follow-ups retaining a valid first result: 0. Actual token counts are reported; no price/cost estimate is invented. Provider prompt caching does not mean a local cached response was substituted.

Raw unassigned: **2834 → 455**. Meaningful unassigned: **2736 → 431**. Unassigned whitespace/page noise: **98 → 24**. All source artifacts, including noise, remain preserved. Counts can change when provider decisions split spans or move assigned content back to unknown; this is not automatically a regression.

Exact extracted-source interval checks: **200/200 passed**. This-run local/review/source-hash bindings: **200/200 passed**. Missing/overlapping output source intervals: 0 in validated artifacts. These checks do not prove original-PDF word coverage or semantic correctness.

## Per-document results

Raw / meaningful counts are shown separately. “All assigned” is a coverage status only.

| Document | Local raw / meaningful | Final raw / meaningful | Requests | Review status |
|---|---:|---:|---:|---|
| A Lokhande.pdf | 11 / 11 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| A Suribhotla.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AMIT_RANA.pdf | 46 / 46 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ANUTOSHTRIVEDI.pdf | 37 / 37 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ARUNSUNDARVENKATARAMANI.pdf | 23 / 23 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AZHARSHAIKH.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AakritiAggarwal.pdf | 37 / 37 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Aarchit Ranjan.pdf | 42 / 40 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AbhishekTiwari.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Abhishek_HV.pdf | 4 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ajay Bandagi.pdf | 7 / 7 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AjinkyaLenekar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AjitSingh.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Akanksha Bhand.pdf | 25 / 25 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AkshataJadhav.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Akshay Wadhwa.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AkshayPatni (1).pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AkshitaKothari.pdf | 19 / 19 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Alvina _Fernandes.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AmenDeebaSiddiqui.pdf | 10 / 10 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Amit Kumar.pdf | 4 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AmitNale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AmmeyUtpatt.pdf | 72 / 57 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AmrikaBhattacharjee.pdf | 28 / 27 | 1 / 0 | 1 | llm_reviewed_all_assigned |
| AmritaRath.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ananya Guha Resume.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AncyImmediatejoiner[8y_1m].pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ankit _ agarwal (1).pdf | 0 / 0 | 1 / 1 | 2 | llm_reviewed_needs_review |
| AnupGurnani[7y_0m].pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Anupam Malte.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Anuradha Yadav.pdf | 14 / 14 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Anuradhika.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Arun Anandan.pdf | 11 / 11 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AshutoshAgrawal.pdf | 32 / 32 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AshwajitWanjari].pdf | 11 / 11 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Asif Hussain Shaik Kovvuru.pdf | 67 / 67 | 30 / 30 | 2 | llm_reviewed_needs_review |
| Assignement.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Assignment.pdf | 25 / 25 | 0 / 0 | 1 | llm_reviewed_out_of_scope |
| AsthaSaraogi.pdf | 11 / 11 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Avinash Kumar Singh.pdf | 41 / 41 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| AvipsaChatterjee.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ayush Sharma.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Bevara Bhargava Krishna.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| BharathKumarP.pdf | 45 / 45 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Bhupendra.pdf | 4 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| CHIGULLA PRASHANT.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| ChaitanyaSareddy.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Chaitra Nayaka.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Chandan_.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Charansai P.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Charansai P_1.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| DEEPAK SINGH CHAUHAN.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| DeepaR.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Deepak Kumar Jha.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Deepak Malik.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Deepak.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Devops Groovy.pdf | 24 / 24 | 25 / 25 | 2 | llm_reviewed_no_sections |
| Dhanraj G Badhe.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Dhiman Mishra.pdf | 2 / 2 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Dinesh Patnaik.pdf | 36 / 35 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Divakar_Prep_guide.pdf | 152 / 147 | 153 / 148 | 1 | llm_reviewed_out_of_scope |
| Diwakar kumar K.pdf | 4 / 4 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Dnyaneshwar NarayanIngale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Dr Shraddha Mishra.pdf | 36 / 36 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Fahad shah M N.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GAJENDRASRATHORE.pdf | 12 / 12 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GAURAV SAWANT.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GAURAVAGRAWAL.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GaneshSirigidi.pdf | 9 / 9 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Gaurav_Batra.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Gauri Shah.pdf | 4 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ghodake Ratnaganga .pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Girish Morab.pdf | 56 / 43 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GopalPrasad K.pdf | 14 / 14 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Gopalakrishna.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| GowthamSelvaraj.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| HARSHAVARDHAN B.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| HarinathReddy.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Harini Sasidharanbai.pdf | 55 / 54 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Hema Kumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Hemant Nikam.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| J SHALINI.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| JEWEL BIJOY.pdf | 0 / 0 | 0 / 0 | 2 | review_failed |
| JYOTI PRAKASH PATRA.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Janardhan.pdf | 6 / 6 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Jasmin Pandya_1.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Jasmin_Pandya (1).pdf | 3 / 3 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Java Aws backend.pdf | 5 / 5 | 8 / 8 | 1 | llm_reviewed_out_of_scope |
| Java Developer & Angular_sanjeev.pdf | 8 / 8 | 40 / 39 | 1 | llm_reviewed_out_of_scope |
| Jitendra Kumar Sahoo.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| K Sreenivasulu.pdf | 8 / 3 | 5 / 0 | 1 | llm_reviewed_all_assigned |
| K_Yugandhar__CV.pdf | 6 / 6 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kadam A.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kalyan_Chakravarthy.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Keerthi_SAPresume.pdf | 0 / 0 | 0 / 0 | 2 | review_failed |
| Keshav - resume.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ketul Sahu.pdf | 4 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| KhalidPathan.pdf | 132 / 132 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Khushal Narain Lulla.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| KhushbooChahar.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| KiranRajR.pdf | 7 / 7 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| KirankumarChidappareddy.pdf | 3 / 3 | 2 / 1 | 2 | llm_reviewed_needs_review |
| Krishnadev_S.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kulwant._Singh.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Kunal Gosavi.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| LIPSA MAJHI.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Lanchana K.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| LikithRaju.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| LohithaBhusarapu.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MA Faisal.pdf | 13 / 13 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MARUTI ANAND CHAMPLI1.pdf | 15 / 15 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Maaz Abdullah.pdf | 49 / 49 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Madan Kumar Singh.pdf | 16 / 16 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MadhukaranAkshayKumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MahaleCharushilaUttam.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mahesh Babu Kadiyala.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mangesh Dhage (1).pdf | 14 / 14 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MangeshPutran.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Manikanta Sanganabhatla.pdf | 4 / 4 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Manisha_Yadav.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Manpreet Kaur.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Manuj Mehrotra.pdf | 52 / 50 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MaritaNikitaDcruze.pdf | 56 / 56 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Md Fazeel Ahmed.pdf | 10 / 10 | 2 / 0 | 2 | llm_reviewed_all_assigned |
| MeghanaPalthepu.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Microsoft_.Net AWS Backend Infra Developers  .pdf | 7 / 7 | 17 / 17 | 1 | llm_reviewed_out_of_scope |
| Mohammed Abbas.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| MohitKumar.pdf | 7 / 7 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mukesh Jha_1.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Mukkadala Ramya Pavani.pdf | 36 / 36 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| NagaSwethaKata.pdf | 29 / 29 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NagaVishnu.pdf | 83 / 81 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nageswar Reddy.pdf | 52 / 52 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NamrataDant.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Naukri_BhushanMhamal[11y_0m].pdf | 37 / 37 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Neeraj Malik.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nikhil Kumar.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Nimisha Susan Varghese.pdf | 9 / 9 | 1 / 1 | 2 | llm_reviewed_needs_review |
| Nisha Singh.pdf | 43 / 43 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NishaPatil.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| NitinKumar.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| P DESHPANDE.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| P.Bala kumar.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PUPPYKUMARI.pdf | 27 / 27 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PallaviSrivastava.pdf | 21 / 21 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pandi Perumal cv.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PankajKumarPatro.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pankaj_Satish_Sharma.pdf | 4 / 2 | 2 / 0 | 1 | llm_reviewed_all_assigned |
| Pavan Bakku.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Phanendra.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Piyush Anand 1.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Piyush Malik.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Piyush.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pooja Fadnavis.pdf | 10 / 6 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Poonam_Muley.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PrabindKumar.pdf | 36 / 36 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pradhap V.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Pradyum Raj_1.pdf | 3 / 3 | 3 / 3 | 2 | review_failed |
| PrajwalS.pdf | 76 / 76 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prakash.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prakash_Gupta_CV.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prasad Hariharan.pdf | 74 / 66 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prasad PR.pdf | 3 / 3 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| PrasadSubhashNanna[7y_5m].pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prasad_Potdar.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| PrashantGupta.pdf | 133 / 133 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Praveen.pdf | 86 / 86 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Preethi_1.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Prescilla Thomas.pdf | 97 / 67 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| PrudhviTejaG.pdf | 0 / 0 | 15 / 15 | 2 | llm_reviewed_needs_review |
| Puneeth v.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| R Sundar.pdf | 6 / 6 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| RIDDHI RAVINDRA BAHIRA.pdf | 3 / 3 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Raja Subramanian.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rajan Dattatraya Dudhale.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| RajatShahBusinessAnalyst_1.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rakesh.pdf | 143 / 138 | 140 / 135 | 1 | llm_reviewed_out_of_scope |
| RakeshKN_1.pdf | 41 / 41 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ravi RS.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| RaviBandaru.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Ravi_RS.pdf | 33 / 33 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Resume_Rituparna Mitra_June 2025.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| RevatiSubhashChorg.pdf | 5 / 5 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| RichaMalhotra_1.pdf | 20 / 18 | 2 / 0 | 1 | llm_reviewed_all_assigned |
| RoashniAdari.pdf | 12 / 12 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| Roshan Dash.pdf | 2 / 2 | 5 / 5 | 2 | llm_reviewed_needs_review |
| RosyPradhan.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| Rutuja Herekar.pdf | 13 / 13 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| S  Abhinav.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| S gaotam.pdf | 24 / 24 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAI KUMAR CHOWDRY.pdf | 6 / 6 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| SAIBABBU.pdf | 10 / 10 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAIPREETHIJUNGA1_3.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SANDHYABR.pdf | 8 / 8 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SANDHYA_KUMAR.pdf | 1 / 1 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SANTHOSH KUMARK.pdf | 8 / 8 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| SARVAGYA.pdf | 2 / 2 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SAYLI_ PACHANEKAR.pdf | 0 / 0 | 0 / 0 | 1 | llm_reviewed_all_assigned |
| SHAIK FATHIMA  RESUME UPDATED.pdf | 1 / 1 | 0 / 0 | 2 | llm_reviewed_all_assigned |
| SHAIK RUSUM MOHAMMAD RASOOL.pdf | 0 / 0 | 0 / 0 | 2 | review_failed |

## Failures and provider uncertainty

**Ankit _ agarwal (1).pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Asif Hussain Shaik Kovvuru.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: ['invalid_assignments']. 30 meaningful spans remain. Local-result retained: False.

**Assignment.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 0 meaningful spans remain. Local-result retained: False.

**Devops Groovy.pdf — llm_reviewed_no_sections**. Provider state: complete; error: none; invalid attempts: []. 25 meaningful spans remain. Local-result retained: False.

**Dhiman Mishra.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Divakar_Prep_guide.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 148 meaningful spans remain. Local-result retained: False.

**JEWEL BIJOY.pdf — review_failed**. Provider state: failed; error: invalid_assignments; invalid attempts: ['invalid_assignments', 'invalid_assignments']. 0 meaningful spans remain. Local-result retained: True.

**Jasmin_Pandya (1).pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: ['invalid_assignments']. 1 meaningful spans remain. Local-result retained: False.

**Java Aws backend.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 8 meaningful spans remain. Local-result retained: False.

**Java Developer & Angular_sanjeev.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 39 meaningful spans remain. Local-result retained: False.

**Keerthi_SAPresume.pdf — review_failed**. Provider state: failed; error: invalid_assignments; invalid attempts: ['invalid_assignments', 'invalid_assignments']. 0 meaningful spans remain. Local-result retained: True.

**KhalidPathan.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**KirankumarChidappareddy.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Microsoft_.Net AWS Backend Infra Developers  .pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 17 meaningful spans remain. Local-result retained: False.

**Nimisha Susan Varghese.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 1 meaningful spans remain. Local-result retained: False.

**Pradyum Raj_1.pdf — review_failed**. Provider state: failed; error: invalid_assignments; invalid attempts: ['invalid_assignments', 'invalid_assignments']. 3 meaningful spans remain. Local-result retained: True.

**PrudhviTejaG.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 15 meaningful spans remain. Local-result retained: False.

**Rakesh.pdf — llm_reviewed_out_of_scope**. Provider state: complete; error: none; invalid attempts: []. 135 meaningful spans remain. Local-result retained: False.

**Roshan Dash.pdf — llm_reviewed_needs_review**. Provider state: complete; error: none; invalid attempts: []. 5 meaningful spans remain. Local-result retained: False.

**SHAIK RUSUM MOHAMMAD RASOOL.pdf — review_failed**. Provider state: failed; error: invalid_assignments; invalid attempts: ['invalid_assignments', 'invalid_assignments']. 0 meaningful spans remain. Local-result retained: True.

## Source, section and relationship concerns

The following are explicit diagnostics, not automatic ground truth. Exact repeated passages may be genuine repetitions. Independent text-parser differences may be reading order, spacing, broken words or missing source text; check the PDF before declaring an omission. Word-boundary splits are concrete source-boundary observations; canonical joined text may still be intact. Relationship flags identify suspicious grouping, not an exhaustive association score.

### A Lokhande.pdf

Source SHA256: `ed940d73d23788e3c7777f7ce246d1894757953e4b1ca9766735481985e3f295`. Source pages present: [1, 2]. API calls 1; tokens 18,735.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### A Suribhotla.pdf

Source SHA256: `620ab3d24d19d580d53bb5973d7d5d029b1cc9aed359d427215990aedd818a55`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 25,922.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AMIT_RANA.pdf

Source SHA256: `e98496f841fdacd4314779cc3f9b51719c2ba0dc3ad8729688a489b247ae0292`. Source pages present: [1, 2, 3]. API calls 1; tokens 36,420.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group; experience-4: multiple_dated_employment_headers_in_one_group Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ANUTOSHTRIVEDI.pdf

Source SHA256: `e32145dc06b21fc56903196401fa57a773655f7706fa74031116d0d37d3aea7b`. Source pages present: [1, 2]. API calls 1; tokens 23,508.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ARUNSUNDARVENKATARAMANI.pdf

Source SHA256: `23f55a652af4a503dd5d7c51b6385df2f9c269310e8cb9445d7bb9f53a87d738`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 58,819.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AZHARSHAIKH.pdf

Source SHA256: `dcf3f4e76bb70f1c56ebff07b7d81b7ab74977bd9ebc90b1709ed7c9db544215`. Source pages present: [1, 2, 3]. API calls 1; tokens 30,476.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AakritiAggarwal.pdf

Source SHA256: `b8f6d33bda4cd400a16b4317d60faa5b51b259d662ed2fb08856d8fe1884e007`. Source pages present: [1, 2]. API calls 1; tokens 25,393.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Aarchit Ranjan.pdf

Source SHA256: `6bd56190bff06524772a0d843141baaec031b9c4eccd7164e85839f8aee75600`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 50,777.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group; experience-4: multiple_dated_employment_headers_in_one_group Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AbhishekTiwari.pdf

Source SHA256: `3b84fabfba1e041abd7193ed348494a4061a610430c8c266dc9d8b6af092191c`. Source pages present: [1]. API calls 1; tokens 14,874.

Section/source flags: independent_pdf_text_difference_requires_source_check.

Repeated-passage candidates: 0; independent-parser unmatched terms: 2; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Abhishek_HV.pdf

Source SHA256: `397e1f6385f58ebe2308c5d836998c38257f2430cedca58a3f192532a19b5726`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 47,751.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 9.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ajay Bandagi.pdf

Source SHA256: `6462281d67c91a043cf95f218aac2539d2479e9b78268a425d0746ebd2ae1cea`. Source pages present: [1]. API calls 1; tokens 15,038.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AjinkyaLenekar.pdf

Source SHA256: `411cdb5b7ce38fec5ee91f55a0908bd75dd75ccd06a2ea5b0e67843bd7290dac`. Source pages present: [1, 2, 3]. API calls 1; tokens 23,915.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AjitSingh.pdf

Source SHA256: `9072566a6a34aca9f17947a3a400f421034b6efc6a5f3a261b5fbe671633ce76`. Source pages present: [1, 2]. API calls 1; tokens 20,853.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Akanksha Bhand.pdf

Source SHA256: `ed58a97537f722d8e884265ff67fa42515479ed8312c8bbd5ef7200607d093ea`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 30,813.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AkshataJadhav.pdf

Source SHA256: `b81d5ae286da8229ea6e33e63985411a56cf70ed6c1379615f87af789208e252`. Source pages present: [1, 2]. API calls 1; tokens 14,993.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Akshay Wadhwa.pdf

Source SHA256: `993946f8484ce1c3b385ca9cd15e5d2390fb73668c41f2485693537c35fb4b68`. Source pages present: [1, 2, 3]. API calls 1; tokens 22,524.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AkshayPatni (1).pdf

Source SHA256: `7f950f0e57892ba655f6601c90bced1679e30bd110c87444a82e937a36594cf4`. Source pages present: [1, 2]. API calls 1; tokens 18,706.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AkshitaKothari.pdf

Source SHA256: `b5122c176b141c5a81b24b7d44544816b2af0b19f846f93d2623145d7452badf`. Source pages present: [1, 2]. API calls 1; tokens 19,423.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Alvina _Fernandes.pdf

Source SHA256: `655dd07fd73e7a35e8663fbee6b2b8204bef1890fbbca42e63afdfbc8c19c386`. Source pages present: [1, 2, 3]. API calls 1; tokens 20,425.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmenDeebaSiddiqui.pdf

Source SHA256: `9742d8a956cb042e8e41ff71ecfe3838fb6bd6a546fd6159a8a0145c858e297f`. Source pages present: [1, 2]. API calls 2; tokens 48,441.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Amit Kumar.pdf

Source SHA256: `ead9fbb058a71add16e553ef8068f9f11daaa702c5d1bfc4d9d261c13b2911db`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 49,149.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmitNale.pdf

Source SHA256: `219e21129f651bb468f829f51043b74ae36d01225560be1dd33d420d3601afc3`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 34,127.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-5: multiple_dated_employment_headers_in_one_group Proposed groups: 10.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmmeyUtpatt.pdf

Source SHA256: `07821a296523d0d353dbe7de3a82fe2713deb7c67025a7cf0508e83dc743dd38`. Source pages present: [1, 2]. API calls 1; tokens 36,104.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmrikaBhattacharjee.pdf

Source SHA256: `e042840e69bb458a11e4d782de7309db979eceef01fe84ec1b7ae9012cead558`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 45,418.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AmritaRath.pdf

Source SHA256: `a150b005a053652fbb44e4e3304fc80dfcc771a446b2c690275f38f97159512d`. Source pages present: [1, 2, 3]. API calls 1; tokens 29,015.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ananya Guha Resume.pdf

Source SHA256: `808f9ed3c7c79527b24e30863a1691d023ca3fb051eece68a11c69ce7b40f8ea`. Source pages present: [1, 2]. API calls 1; tokens 16,903.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AncyImmediatejoiner[8y_1m].pdf

Source SHA256: `7265001b1f14e7ecf42912c1f4923370742b60d333f6f4e754a7e0f25832b902`. Source pages present: [1, 2, 3]. API calls 1; tokens 24,255.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ankit _ agarwal (1).pdf

Source SHA256: `f83463b281e1f7597c751a24fbb4d1379b36a6e0acbcca8fa293e1bc78ed9f50`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 56,125.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: multiple_dated_employment_headers_in_one_group Proposed groups: 7.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AnupGurnani[7y_0m].pdf

Source SHA256: `122acdd99f6a0ee553537bc746d2e5d8d32531c41e52a0598237e4e020902917`. Source pages present: [1, 2]. API calls 1; tokens 20,621.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Anupam Malte.pdf

Source SHA256: `ada289f6e3723f815640a558fe27fa9d3799fcac9a9219c748c057666051275c`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 26,835.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Anuradha Yadav.pdf

Source SHA256: `60484622d8466a2e242f2cc097d78747f051cb7174484ae06bfe6bb0375aca5a`. Source pages present: [1, 2]. API calls 1; tokens 14,549.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Anuradhika.pdf

Source SHA256: `117e559c970205e2079477f5449e1bb983a95dea10565054dfdeb59252b249c0`. Source pages present: [1, 2]. API calls 1; tokens 25,518.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Arun Anandan.pdf

Source SHA256: `c3162633e6587481b768979020a621caf30a4c51d9dea2424588814193421596`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 61,272.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 10.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AshutoshAgrawal.pdf

Source SHA256: `99f693621e15b6e1671b7d207aa5a1e30ccc16a108899a3494793b62f3186591`. Source pages present: [1, 2]. API calls 1; tokens 21,907.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AshwajitWanjari].pdf

Source SHA256: `332ad12bec198513308b033d8a9bbb92043e8e091a971ad0d47b2930853d4ae3`. Source pages present: [1, 2]. API calls 1; tokens 17,414.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Asif Hussain Shaik Kovvuru.pdf

Source SHA256: `9ce6951e681944ec0df4d355584c3fe31bac2d188068de29b1cdb680cd39651f`. Source pages present: [1]. API calls 2; tokens 56,749.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Assignement.pdf

Source SHA256: `2813113fdc6690cfc532461220ebcda4ce7eea97c8e0857fbe8b2e15d9f431f1`. Source pages present: [1]. API calls 1; tokens 7,795.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Assignment.pdf

Source SHA256: `010745684c449b883e813e1f81362c77825882c541977ba91a88e990f4cc2e79`. Source pages present: [1]. API calls 1; tokens 5,815.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AsthaSaraogi.pdf

Source SHA256: `83e6affd3c36a2b7b17f82e0096b156d65f5cfaa0a986a3d6fca35ee15493435`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 54,886.

Section/source flags: extraction_duplicate_candidates_require_source_check.

Repeated-passage candidates: 2; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Avinash Kumar Singh.pdf

Source SHA256: `1144f7ec741d4d3314d3979ea712f4de08c4202d925df793560fced19f0e2923`. Source pages present: [1, 2, 3]. API calls 1; tokens 32,378.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### AvipsaChatterjee.pdf

Source SHA256: `05580c10b818064a1881e8b1b2a75eb080c956a825c15076e9ac116e14ca7839`. Source pages present: [1]. API calls 1; tokens 12,317.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ayush Sharma.pdf

Source SHA256: `648b1186b9d0c53aac629a89332b5f6ce5c71bf7b6587cbf85ede7624fc31931`. Source pages present: [1, 2]. API calls 1; tokens 17,183.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Bevara Bhargava Krishna.pdf

Source SHA256: `1ea9a3ac3ad5b00f28ef4bea071958ec8cffc3354f3f1312dff04c7fe86d4824`. Source pages present: [1, 2, 3]. API calls 1; tokens 37,233.

Section/source flags: independent_pdf_text_difference_requires_source_check.

Repeated-passage candidates: 0; independent-parser unmatched terms: 1; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### BharathKumarP.pdf

Source SHA256: `d10bdd0e2d32c581c38fc11fa2535c4b4e1940806b74256efd9af772d730560e`. Source pages present: [1]. API calls 1; tokens 13,229.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Bhupendra.pdf

Source SHA256: `63618c9188e3c8d4a9c4ef5898dc180401cb5a0940709e44af8fcd9f7e4514d2`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 54,392.

Section/source flags: extraction_duplicate_candidates_require_source_check; education_relationship_concerns.

Repeated-passage candidates: 1; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 18.

Education: education-6: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 6.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### CHIGULLA PRASHANT.pdf

Source SHA256: `e0470ff9f6a67fb6bf726a8f931516d379aa0546a863fcd14fb6d91fd3dfc132`. Source pages present: [1, 2, 3]. API calls 1; tokens 29,929.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### ChaitanyaSareddy.pdf

Source SHA256: `8238d23e03b0beabf2356a8bd53ee9b98a50ca1a6c702b4e65439ca3df64cdd0`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 35,947.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: artifact_only_entry Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Chaitra Nayaka.pdf

Source SHA256: `1304c61b7684a580e5edc2be235e8892318d45b9dad639cc2955755809352970`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 40,866.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Chandan_.pdf

Source SHA256: `6e0e105d369589a86215b50a12eb41da9498fca10d92de64a4605a05a7d5a3e8`. Source pages present: [1, 2, 3, 4, 5, 6, 7]. API calls 1; tokens 49,100.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Charansai P.pdf

Source SHA256: `cc435e0166b283e4e32650b799ee526b1a3bc0dcb1c0819ebecda40ae90437e3`. Source pages present: [1, 2, 3]. API calls 1; tokens 31,381.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Charansai P_1.pdf

Source SHA256: `afbce3d01981bd91bfac71e9e5e0b18e556c60d3e210c3994a32ad11568f91b8`. Source pages present: [1, 2, 3]. API calls 1; tokens 31,381.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### DEEPAK SINGH CHAUHAN.pdf

Source SHA256: `558f959872acf59d155317b916b5428cb4b65758145490e078550a8bcf5d7eae`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 24,318.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-6: multiple_dated_employment_headers_in_one_group Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### DeepaR.pdf

Source SHA256: `5bce56951525b124f6021414b32dd206bc299f819e72ce2ab3a0fe2753a62f36`. Source pages present: [1, 2]. API calls 1; tokens 18,722.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Deepak Kumar Jha.pdf

Source SHA256: `a13bc2eaeeb62b7b815e5ae4ec9c0cdef5455409a457768de8e5e4d48b4092c7`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 44,198.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Deepak Malik.pdf

Source SHA256: `20a95d0318f6fe4fad437cb38e6cf8884c3074a0959e607960a7f2f452c0f73c`. Source pages present: [1, 2]. API calls 1; tokens 16,958.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Deepak.pdf

Source SHA256: `7c3e058907c91ababe575a638463ca64db3d227e957d1d970738b913a3cfb651`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 37,625.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 11.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Devops Groovy.pdf

Source SHA256: `5ee46d04d0f25744dfca5bea017f7b6efa293872df39081ab67509b637017b21`. Source pages present: [1]. API calls 2; tokens 10,667.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dhanraj G Badhe.pdf

Source SHA256: `5da61283511fdcd74aac8cc1b95fda4b314a22f96c8c36e95b5c4d0e4e107155`. Source pages present: [1, 2, 3]. API calls 1; tokens 28,827.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dhiman Mishra.pdf

Source SHA256: `743b5cb037c69a20776200c737bf2ce7cf6c6d254bfd6c3e4483dcff8f775e76`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 55,207.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dinesh Patnaik.pdf

Source SHA256: `f29e599cca3a10fdaae4a5de0c971e47e83b4b342c40f331c2400a695110e9dc`. Source pages present: [1]. API calls 1; tokens 18,014.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Divakar_Prep_guide.pdf

Source SHA256: `28f6fb290df57439f44528c7958ec85e721d944b42a1ff66a6418765bdf9d265`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 32,444.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Diwakar kumar K.pdf

Source SHA256: `6b4ffa8ea25245f8517eaff8e456c3115a13daedf6a8a406dc904f2473d96535`. Source pages present: [1]. API calls 2; tokens 39,032.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dnyaneshwar NarayanIngale.pdf

Source SHA256: `850ec405810adb1222c4dd3766940847fb75497d187f177df4dd0b740db40526`. Source pages present: [1, 2]. API calls 1; tokens 15,509.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Dr Shraddha Mishra.pdf

Source SHA256: `31bb5f4bd5709d9273e78191f84d6e45be66b3e182d7edf93c08c027603c85c3`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 56,463.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-5: multiple_dated_employment_headers_in_one_group Proposed groups: 6.

Education: education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Fahad shah M N.pdf

Source SHA256: `68dc8543e11f3af379c565270053c3a8da2276c7a1a007b74c3e54e1ff5532f4`. Source pages present: [1, 2]. API calls 1; tokens 12,624.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GAJENDRASRATHORE.pdf

Source SHA256: `be67d2f315b68262c0f83f886c51a1d5b1d3b2319b7d4a87d227a82233846818`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 52,893.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GAURAV SAWANT.pdf

Source SHA256: `f1ea49d63ff6a178f0f967688f3db6091f1e298c791339e61206b2230e32b996`. Source pages present: [1, 2, 3]. API calls 1; tokens 25,670.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GAURAVAGRAWAL.pdf

Source SHA256: `9bbcb0781eecdd553e6ce120b8a33e889436fd65c5c445854112345b84b08ac6`. Source pages present: [1, 2]. API calls 1; tokens 16,221.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GaneshSirigidi.pdf

Source SHA256: `7f2dc62d0fe141c7b89a393b966c92be1ea1bf8297ba53fd54a287b95f0c5423`. Source pages present: [1, 2]. API calls 1; tokens 19,758.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Gaurav_Batra.pdf

Source SHA256: `09379e06863e3f703732f26f7647a3e383633480e6be2b11bbd7e44523c0817a`. Source pages present: [1, 2, 3]. API calls 1; tokens 23,169.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Gauri Shah.pdf

Source SHA256: `85b8f7a571b208dd2c3325950cf31e3f4b6e26b0994a909ffcf6022f3dda6b30`. Source pages present: [1, 2]. API calls 1; tokens 20,351.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ghodake Ratnaganga .pdf

Source SHA256: `c0b2b7f0284b2ae86b49126ea626e9d785c19c256e3a04d21e070796ff96d89a`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 43,682.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Girish Morab.pdf

Source SHA256: `b9e510607779fa6d259accdfd7c3c99b2f54598bc870d9e1cb564f55d0d7fab0`. Source pages present: [1, 2, 3]. API calls 1; tokens 44,647.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GopalPrasad K.pdf

Source SHA256: `863a82d120c468c8e3c88fa7c43a80aa16c9485e8a570b8dcee8d9dc5bc69c4b`. Source pages present: [1, 2, 3]. API calls 1; tokens 38,757.

Section/source flags: independent_pdf_text_difference_requires_source_check; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 34; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-2: numeric_or_grade_only_entry Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Gopalakrishna.pdf

Source SHA256: `cc7fdbd297b9246c06b2beb8736997ba0b1291606a3c5b8c8467455ee3be0302`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 47,564.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### GowthamSelvaraj.pdf

Source SHA256: `2e96285ea903ae02b62cc1fcbbd3b74bcf172ca5d1fcf0c5873f7790b455847e`. Source pages present: [1]. API calls 1; tokens 16,473.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### HARSHAVARDHAN B.pdf

Source SHA256: `6d813cd9c61bd1c6586aa74c1a9869cd87e404e62418af535715c9d935588864`. Source pages present: [1, 2, 3]. API calls 1; tokens 16,821.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### HarinathReddy.pdf

Source SHA256: `8785fd636a3d562c0b463035b1a9f2d0289eeebd8de490d9c02e8e15bda4cc37`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 32,100.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Harini Sasidharanbai.pdf

Source SHA256: `ca3547c50ae7421b006861b9bf0fe9450bac95177c201c188231aca372609d13`. Source pages present: [1, 2]. API calls 1; tokens 17,418.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Hema Kumar.pdf

Source SHA256: `d0511944f1463e58f80f9f6af341035fcb68d4a16bd85b2aff2ce1b5df6c8cde`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 24,831.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Hemant Nikam.pdf

Source SHA256: `f27a0fdc416ce936074ba0a63ca0d63943e07c9221d530efcd5e906fbb83b7ff`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 38,329.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### J SHALINI.pdf

Source SHA256: `46266bde6b2beb9f83167e0c4da624a91f0adbe4b1215aea6b2d1f5cb156adb1`. Source pages present: [1, 2, 3]. API calls 1; tokens 29,783.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### JEWEL BIJOY.pdf

Source SHA256: `80928a1e33177a4d20dda72f011c720ffc39c895057d6c9ee2bf89da4920e510`. Source pages present: [1, 2]. API calls 2; tokens 32,760.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; provider_review_failed_local_result_retained.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-19: numeric_or_grade_only_entry Proposed groups: 19.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### JYOTI PRAKASH PATRA.pdf

Source SHA256: `54ccb811d8a897a7dc6053e7f0914f2f0d0fa7602f2ad4e0cb32482fa9de8c6e`. Source pages present: [1, 2]. API calls 1; tokens 22,264.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Janardhan.pdf

Source SHA256: `45015e8c69532793329955826c103211ad5041fb378d5a338d034258bcdf527e`. Source pages present: [1, 2]. API calls 2; tokens 63,703.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Jasmin Pandya_1.pdf

Source SHA256: `cdcfe239cebe1c604d3adba5b3d39966e1e175c5d903ddbe821435446f0d95b1`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 39,602.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Jasmin_Pandya (1).pdf

Source SHA256: `47a2ccde8e20a10c29255d2c23ba4ce1aae340daaef5f3687091e924d58a382a`. Source pages present: [1, 2, 3]. API calls 2; tokens 50,728.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Java Aws backend.pdf

Source SHA256: `a829c05aa18916dce49096991a37e28a470d28c3effd5a7132f7e6b15af6f218`. Source pages present: [1, 2]. API calls 1; tokens 10,392.

Section/source flags: out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Java Developer & Angular_sanjeev.pdf

Source SHA256: `0001fd97e8314265a495d8d70aa83ec1196240c3be2518eba5dd90758e82066e`. Source pages present: [1]. API calls 1; tokens 8,621.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Jitendra Kumar Sahoo.pdf

Source SHA256: `22768daba2a65214d2c0be47954949566e67c5bafac357af06cdb6542f8e47ec`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 47,215.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### K Sreenivasulu.pdf

Source SHA256: `ae5fb209de37c0c23ea428e7f18a1328461ef19aa7f0802fa8bb5caa30054278`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 45,298.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### K_Yugandhar__CV.pdf

Source SHA256: `5b385603648a26deb25a1274bee4c05e664bfe9a4b8473708eb015469efe181a`. Source pages present: [1]. API calls 1; tokens 17,501.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kadam A.pdf

Source SHA256: `ea195de3d818a37c3589602b5cff84683089edfde7b5268a9c7389b8f957c806`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 20,960.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 10.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kalyan_Chakravarthy.pdf

Source SHA256: `f52962091adad4e4a9eccf04706cdd07546a6b032ab9de351407e1d555d7756d`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 35,363.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Keerthi_SAPresume.pdf

Source SHA256: `ad5e648e21102bce534924ab7c5a0e196ed0b56663189d05fce6e9f83c823750`. Source pages present: [1]. API calls 2; tokens 11,853.

Section/source flags: independent_pdf_text_empty_requires_visual_or_ocr_reference; provider_review_failed_local_result_retained.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Keshav - resume.pdf

Source SHA256: `84a04f3a1d2b30daaa95784801dbdf4f8c3cf8e0bbfd3f048cdc115651ff8cd2`. Source pages present: [1]. API calls 1; tokens 8,989.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ketul Sahu.pdf

Source SHA256: `486ea26a044045158c1c648850a8d07cd93d3053e55930dcdd3bfbf25551e096`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 55,427.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 13.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### KhalidPathan.pdf

Source SHA256: `a12eb0d5cf74a50c893cae0707a7d5826f2628aa7e6606c4a337d4df11faa3b1`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 84,431.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Khushal Narain Lulla.pdf

Source SHA256: `6ebae0c3da8a6bddb82ceecd7dd00bf7a8515dfda685f70f4fc7297a8af16ce1`. Source pages present: [1]. API calls 1; tokens 10,596.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### KhushbooChahar.pdf

Source SHA256: `9d9b6bf5da4d5f89159a6ee1fc1959eba378acae032a54826b15ba9b229f3ab0`. Source pages present: [1, 2]. API calls 1; tokens 23,633.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### KiranRajR.pdf

Source SHA256: `51c333bf30b7c4b7cf141c57c652cd47a066585ea1dfddaa9768a1f794d3cf0f`. Source pages present: [1, 2, 3]. API calls 1; tokens 33,415.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### KirankumarChidappareddy.pdf

Source SHA256: `b2085888703d3d27292923564a287460273e1f06eeb961780a44a632d787595f`. Source pages present: [1, 2, 3]. API calls 2; tokens 50,531.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Krishnadev_S.pdf

Source SHA256: `46511b668f2663bce892111ee9c68bb15f1e429435a6e24dbd90f456a1cf82e5`. Source pages present: [1, 2, 3]. API calls 1; tokens 29,362.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kulwant._Singh.pdf

Source SHA256: `7c04045cda7528b50c3a136468d772ea89cc8cc8bf0af599d8eb80df1506f09f`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 36,652.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Kunal Gosavi.pdf

Source SHA256: `ca7b3534805e9dddada5e424ab4e4c64d6dff4cd8b6378aca2c5c5ea4db17d64`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 28,632.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### LIPSA MAJHI.pdf

Source SHA256: `144a66fd07d7c98329f2b0e6e119facf6510f8fbf49e62b4975b4a8d9a6924be`. Source pages present: [1, 2, 3]. API calls 1; tokens 25,311.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Lanchana K.pdf

Source SHA256: `8633132a4cab4928dd5c2f78b509f9e4d6c3a6a5f61064d7c33fbc6093e901e3`. Source pages present: [1, 2, 3]. API calls 1; tokens 27,913.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### LikithRaju.pdf

Source SHA256: `3d3d344063b0a3caa73604841c3b12512916420124d1a6f50e7be98b925eeb3c`. Source pages present: [1]. API calls 1; tokens 12,272.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### LohithaBhusarapu.pdf

Source SHA256: `632c6a037df53d8760cac6e6c68cc4b582e195fd03fe601583099936658bfcf2`. Source pages present: [1]. API calls 1; tokens 16,095.

Section/source flags: independent_pdf_text_difference_requires_source_check.

Repeated-passage candidates: 0; independent-parser unmatched terms: 1; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MA Faisal.pdf

Source SHA256: `00596d57717d783e92a67f71174ff44425d8fd5f53c5e24a3799540484e0fa36`. Source pages present: [1, 2, 3]. API calls 1; tokens 45,692.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MARUTI ANAND CHAMPLI1.pdf

Source SHA256: `59c358d22246a00349bf79b7fa5a1760f40688a7f8ff95bd8b559e77c8413545`. Source pages present: [1]. API calls 1; tokens 25,622.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Maaz Abdullah.pdf

Source SHA256: `56d90625b515015989f2adec949c97ac4372e0508b0649529d31f0c3392a6dcf`. Source pages present: [1]. API calls 1; tokens 11,898.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Madan Kumar Singh.pdf

Source SHA256: `e2db3e4c0be734d114a121d2a14023ce50bfb0f84650443bb6184d61ba29c12d`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 54,291.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MadhukaranAkshayKumar.pdf

Source SHA256: `5a802722825cc272a36da66eff0d07c7d2a11368ed3d3098ccbdbc71bea92b17`. Source pages present: [1, 2, 3]. API calls 1; tokens 31,570.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MahaleCharushilaUttam.pdf

Source SHA256: `0ed2019a297e6a8bfecfa265ecf24c1bf6781be45ca7453ca2e4e3e303b37f10`. Source pages present: [1, 2]. API calls 1; tokens 22,673.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mahesh Babu Kadiyala.pdf

Source SHA256: `bee3ff8e87e081327c09f045498a993f349bdc5007b32be2fd66da0245b1ba9d`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 38,300.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mangesh Dhage (1).pdf

Source SHA256: `61ea9dab564c8a7c83fcdb59aff6ec0d722b4c486814f81fe42a62275772044e`. Source pages present: [1]. API calls 1; tokens 12,287.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MangeshPutran.pdf

Source SHA256: `b49447fb5a5648c2c9f138188c8f614d82ce7fe2ec22b1df1cdf39953ef9f0d9`. Source pages present: [1]. API calls 1; tokens 13,403.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Manikanta Sanganabhatla.pdf

Source SHA256: `85f73d2041a8691bd5fe1ec68e59cde6d055a257681b49ff0f03aa19939b2d70`. Source pages present: [1, 2, 3]. API calls 1; tokens 31,530.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Manisha_Yadav.pdf

Source SHA256: `9f6c168feb5fb79cec0108f9e398d66183359e4cd165afc1b8c8f87cb13afc0e`. Source pages present: [1, 2]. API calls 1; tokens 11,666.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Manpreet Kaur.pdf

Source SHA256: `7833d96d38cfa8382c61f57d89c783901071d235530f99be44011f23770924a7`. Source pages present: [1, 2]. API calls 1; tokens 19,071.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-5: multiple_dated_employment_headers_in_one_group Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Manuj Mehrotra.pdf

Source SHA256: `805767d9a7d5a88beb00333ce5058ab087974211ffefaf58c04c48a8d3375972`. Source pages present: [1, 2]. API calls 1; tokens 21,978.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MaritaNikitaDcruze.pdf

Source SHA256: `054387c4a9c1f1efe127e7db6b62076ffa7e64e6cb4fad84632933ff289ed8ee`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 39,229.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review; education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Md Fazeel Ahmed.pdf

Source SHA256: `0974d9d471f5c1c3c3ed535af3ef25260f4c3136b11d8047faf3669c1f6c4434`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 62,174.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MeghanaPalthepu.pdf

Source SHA256: `a29e34a7f1aef50cff64b91844039aeb79d4c3e5fb455a44bf935c86f93dd051`. Source pages present: [1, 2, 3]. API calls 1; tokens 26,777.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Microsoft_.Net AWS Backend Infra Developers  .pdf

Source SHA256: `9c9644d433a0b0e7312c9881c7773acb03d73fed7936a864c05a8178004115f7`. Source pages present: [1]. API calls 1; tokens 10,085.

Section/source flags: out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mohammed Abbas.pdf

Source SHA256: `135d74001ec22d9098eba2d7d1598a137e3cc68d046cb5e522a3ae4f8ea8c8cf`. Source pages present: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]. API calls 1; tokens 179,513.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 17.

Education: education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### MohitKumar.pdf

Source SHA256: `7b013f239443c10e1d9b31975380f9c286d97e183f73857db518edfe3fe16533`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 39,321.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mukesh Jha_1.pdf

Source SHA256: `61d01c221976dacf2420ab87f8361dc4f185ab7bcfdbea93d9f9d17364010442`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 40,013.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Mukkadala Ramya Pavani.pdf

Source SHA256: `634b0c3473c81fc649d8475268b79b5a5bc978258adeed99d835ef46f8565307`. Source pages present: [1, 2, 3]. API calls 2; tokens 39,821.

Section/source flags: source_word_split_across_output_blocks.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 2.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NagaSwethaKata.pdf

Source SHA256: `17ed938204e437183f93ada9c4d9ff30ed8a3ac6effd2137588df657ee33138c`. Source pages present: [1, 2, 3]. API calls 1; tokens 39,232.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NagaVishnu.pdf

Source SHA256: `b48a8a2bdc960608e092beac6d03120ea9fcddb7e46d894281578f99dadf335e`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 45,125.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nageswar Reddy.pdf

Source SHA256: `af063923753f1814d2a21046e1a61c70e542d774b6356e79af8938121f29f558`. Source pages present: [1, 2, 3]. API calls 1; tokens 37,839.

Section/source flags: independent_pdf_text_difference_requires_source_check.

Repeated-passage candidates: 0; independent-parser unmatched terms: 1; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NamrataDant.pdf

Source SHA256: `4b6e27014f1845ffbb8ed9cb142d2f42389f77fb0859a2b45760786e8abb9734`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 34,412.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Naukri_BhushanMhamal[11y_0m].pdf

Source SHA256: `84d7699ba27c31c7b4475d13b80f7e317d35bd2efc59056ca4adb273a58e9e1d`. Source pages present: [1, 2]. API calls 1; tokens 37,078.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Neeraj Malik.pdf

Source SHA256: `4714be1bb3b42393c9e327575aa3ea193efbf96465bc70cc33ec0a43b478ba37`. Source pages present: [1, 2]. API calls 1; tokens 25,691.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nikhil Kumar.pdf

Source SHA256: `73c78b61ec58b86210ae4f288a8a90ef9ff06d1af428786f49046ca29d700b42`. Source pages present: [1, 2, 3]. API calls 1; tokens 28,183.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nimisha Susan Varghese.pdf

Source SHA256: `e938b2f7006dfe367dcadf47e96f7fdc02580f4a5cf40e0249b34de2a931d966`. Source pages present: [1, 2]. API calls 2; tokens 34,897.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Nisha Singh.pdf

Source SHA256: `039047878ed3e33f14ebc4d686017d1a1d972f5466e7b0c94dee4931dc2dbaff`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 58,002.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NishaPatil.pdf

Source SHA256: `f8fc3efd8853b4171c2398283686aaa331723fc9c94ab42e68858ca79513fe42`. Source pages present: [1, 2]. API calls 1; tokens 14,331.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-3: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### NitinKumar.pdf

Source SHA256: `e5aa2942dfe1d2a75cf8f694c951d058d8a463ba230db00a50b9a419412a3551`. Source pages present: [1, 2]. API calls 1; tokens 12,619.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### P DESHPANDE.pdf

Source SHA256: `a9b338cfda818602c7c3834611454f81fc5781ce1e2f6b8c6b5e257b31d37cf4`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 37,085.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### P.Bala kumar.pdf

Source SHA256: `4feee8ef9dfb9c62f6ad6d81d0ffe10e90ba2d0dce27cbd8e3d1399cdd7c0681`. Source pages present: [1]. API calls 1; tokens 12,055.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PUPPYKUMARI.pdf

Source SHA256: `28b2147dc8895b94a1c7eacd52d2974aea75ca84408a6bed0ebc12efac55d538`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 63,910.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-2: numeric_or_grade_only_entry; education-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PallaviSrivastava.pdf

Source SHA256: `c0dc3f1e010792220cd4eb4a86988aafa0c0dadd090d691054df0bda86105990`. Source pages present: [1, 2, 3]. API calls 1; tokens 27,454.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pandi Perumal cv.pdf

Source SHA256: `70d8cc3717d54d17970ee23416f3d124ad88713f30f4f57d1c6613444cf771ba`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 48,086.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PankajKumarPatro.pdf

Source SHA256: `e5e38efedfb08aa89bedfe4d05a45d3578e9ad1762410a1340f4069f76e8f5dc`. Source pages present: [1, 2, 3, 4, 5, 6, 7, 8, 9]. API calls 1; tokens 70,657.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pankaj_Satish_Sharma.pdf

Source SHA256: `6f65708accc48c1b0e3122096eca60971734520c9dc14edb180ca6b6011703f0`. Source pages present: [1, 2]. API calls 1; tokens 15,980.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pavan Bakku.pdf

Source SHA256: `9cd414d78c4fb79f01adea54f62150e573a07892987e008d5bc167962bc3c203`. Source pages present: [1]. API calls 1; tokens 15,266.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Phanendra.pdf

Source SHA256: `b4495bee59a20d277893f8078e140a81d31266cf099b44515c837285937fa898`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 42,998.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Piyush Anand 1.pdf

Source SHA256: `8092e443779e3f5874c410ef4b82ad4771477665fb13055c4fe07288587b9329`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 28,697.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 12.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Piyush Malik.pdf

Source SHA256: `538be70d992142407dff2394e7a50517c579a9a6f004279ad13e5008a2ae6bd8`. Source pages present: [1]. API calls 1; tokens 16,130.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Piyush.pdf

Source SHA256: `efc65516d55ae70b98f8854d45ac244d31e037a552031b21fcd8cef2fdba05f2`. Source pages present: [1]. API calls 1; tokens 13,044.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pooja Fadnavis.pdf

Source SHA256: `8ee17102d3b1c2ac1fe92faedeb8aed7d07815f69f084c70bfb5b42ce4d22649`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 47,412.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Poonam_Muley.pdf

Source SHA256: `0399f6417ff6c3b7c9bda35bef22aafc0ad7026741ce740a6592de98f0e66473`. Source pages present: [1, 2, 3]. API calls 1; tokens 22,324.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrabindKumar.pdf

Source SHA256: `3670d9c0efb9a5ed5872948970fa8355adbc770d14fb04beb16197666d30ebe2`. Source pages present: [1, 2]. API calls 1; tokens 26,193.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-4: multiple_dated_employment_headers_in_one_group Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pradhap V.pdf

Source SHA256: `a29c7fabaaf6a7348cafe658b27202ce52244a7d9f27039ae4a8383503eca76f`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 36,074.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Pradyum Raj_1.pdf

Source SHA256: `782e34f73e083f72955546cf99a587d4f9ad20af7a4325556143c95a0ceb7ab5`. Source pages present: [1]. API calls 2; tokens 38,178.

Section/source flags: employment_relationship_concerns; provider_review_failed_local_result_retained.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates; experience-4: artifact_only_entry Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrajwalS.pdf

Source SHA256: `59e27a9b16e9cbbfcf8658adb31fe9c5619db96fccdc9c3da2d23281265556ca`. Source pages present: [1, 2]. API calls 1; tokens 19,561.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prakash.pdf

Source SHA256: `c3446699c5521b9afd0d2f21d20516e4f7c9e1d3c599af15f578235b857911c6`. Source pages present: [1]. API calls 1; tokens 17,843.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prakash_Gupta_CV.pdf

Source SHA256: `d45cb9216caff59749a17b9efe8f58dcc1445baefb505de9776a31de538d9c74`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 33,109.

Section/source flags: employment_relationship_concerns; education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: multiple_dated_employment_headers_in_one_group Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prasad Hariharan.pdf

Source SHA256: `047cd6e63e176bc12bc998b2f1fbe39b44d22826c27b7b95f49796152cd5ee3f`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 70,652.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: education-2: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prasad PR.pdf

Source SHA256: `1a18a9aae06b32eeb868a04b5a3819c06299f9f9affc7d84cc536c99bf4e5609`. Source pages present: [1, 2]. API calls 2; tokens 33,419.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrasadSubhashNanna[7y_5m].pdf

Source SHA256: `5c9e4b017e81df8240f3805212ea60ec8da18977e17d6d337832658980de4c9b`. Source pages present: [1, 2, 3]. API calls 1; tokens 27,289.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prasad_Potdar.pdf

Source SHA256: `a7e9f53513bb4c5a1304508600c7dbeda9adaa237b39c9becca2c7bb36360d7d`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 49,843.

Section/source flags: independent_pdf_text_difference_requires_source_check.

Repeated-passage candidates: 0; independent-parser unmatched terms: 1; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrashantGupta.pdf

Source SHA256: `a348d01d85de549c51cdf1e3f3d825ea7c342a007478ebdb1ac5e0b0d76135a4`. Source pages present: [1, 2, 3]. API calls 1; tokens 30,875.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Praveen.pdf

Source SHA256: `c3287e2ba313eb1cf8d0c3ad06f899ca72811585dacb56bf272610c4b66dc63a`. Source pages present: [1, 2, 3, 4, 5, 6, 7]. API calls 2; tokens 159,104.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 8.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Preethi_1.pdf

Source SHA256: `3ca902dc1977232015ebdafbba9ff78be0f868ed63cf1a693b9f7b6c66b5a66c`. Source pages present: [1, 2]. API calls 1; tokens 14,958.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-2: date_only_entry_possible_detached_dates Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Prescilla Thomas.pdf

Source SHA256: `45523bf70055191f8a1a3c1f4fd5574a6d474d83164ba380406ed16cebfd607c`. Source pages present: [1, 2, 3]. API calls 2; tokens 87,457.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### PrudhviTejaG.pdf

Source SHA256: `bd49fcfd3fb311353e56c2f5328a5941eaa06b039cc017ce7b2f05ced18fbe4e`. Source pages present: [1, 2, 3, 4, 5]. API calls 2; tokens 100,855.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Puneeth v.pdf

Source SHA256: `60a9d73772a7c5ec21c92b55d0ffe554e8958e4759023a7413bcd523e4ff3acc`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 34,058.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### R Sundar.pdf

Source SHA256: `8f576b4267573b1f1a36660ab62177fb7f7da56dff2706da0b892a5ce1d0db77`. Source pages present: [1]. API calls 1; tokens 16,785.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RIDDHI RAVINDRA BAHIRA.pdf

Source SHA256: `9b30a93b62241d7194a3a5a2bd564878286276323a6703980c2863a970055611`. Source pages present: [1]. API calls 1; tokens 11,969.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-2: numeric_or_grade_only_entry Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Raja Subramanian.pdf

Source SHA256: `acce1288f01b84d514e7ca56bf9caf57762c5caaa58ed00f3c3ddbb5aadd966a`. Source pages present: [1, 2, 3, 4, 5, 6, 7, 8]. API calls 1; tokens 80,955.

Section/source flags: extraction_duplicate_candidates_require_source_check; education_relationship_concerns.

Repeated-passage candidates: 1; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rajan Dattatraya Dudhale.pdf

Source SHA256: `935e9952b655fa4620cdfb4c9fd98aa28d4794c490b5e4e4192c2c0d8b34f9a0`. Source pages present: [1, 2, 3]. API calls 1; tokens 23,023.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RajatShahBusinessAnalyst_1.pdf

Source SHA256: `224d8db0a4f82dff72a933537e853d48e77c5e3f9bc1d9309439d0b75c466388`. Source pages present: [1]. API calls 1; tokens 18,100.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rakesh.pdf

Source SHA256: `e6d90754647f85270932e52d022b05d4ae2deadba6f2fd17b12571b73efd453e`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 30,527.

Section/source flags: employment_relationship_concerns; education_relationship_concerns; out_of_scope_job_requirements.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RakeshKN_1.pdf

Source SHA256: `1683bbd62c5186971f7689d58cb5c87eea86c2c1309eb266a25b8fde91e640e7`. Source pages present: [1]. API calls 1; tokens 20,386.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: date_only_entry_possible_detached_dates Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ravi RS.pdf

Source SHA256: `b22e98c77fe9c93d2d72ec2163a7db8322ede0ad3411c76da724a87217c177ff`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 38,237.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RaviBandaru.pdf

Source SHA256: `35131220db8bc49453d39e0efed4524551b0d6942e45c76ec337d35fa1af9e9e`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 41,222.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Ravi_RS.pdf

Source SHA256: `2b4ff151bcf26d9fc7f899cb4fcc46eeadca97c60c79599ee6bec1191476a86b`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 47,395.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 5.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Resume_Rituparna Mitra_June 2025.pdf

Source SHA256: `23b6582003fcf2cd9a90ba941a4c769acd1f31c6d6cd363fcfb99ed6fb7925a3`. Source pages present: [1]. API calls 1; tokens 11,480.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RevatiSubhashChorg.pdf

Source SHA256: `3846ac323b1f575023ce085595a1eb6220d68e8f79c8b8bd632b4bd9fb8000e6`. Source pages present: [1, 2]. API calls 1; tokens 26,449.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 9.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RichaMalhotra_1.pdf

Source SHA256: `58ff58dada7dd6cf55a843ee5d659fc1011cb4f3a726fef620a222a8ce2b9ccc`. Source pages present: [1, 2, 3]. API calls 1; tokens 24,131.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No proposed education groups; original PDF review required Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RoashniAdari.pdf

Source SHA256: `c4f837c91a1cf1cd31b91eb3a99342106ed4ef3b3b0649a3b673fdc05243fc4d`. Source pages present: [1, 2]. API calls 2; tokens 62,755.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Roshan Dash.pdf

Source SHA256: `63401921d2202e2b91a57ec50a9314af093067668c92ec90ff181a442be2464a`. Source pages present: [1, 2]. API calls 2; tokens 33,575.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### RosyPradhan.pdf

Source SHA256: `424dceb0810a3c532fb4917a7dc393d5b5f5baf460b91a32b73a89b21b4e8704`. Source pages present: [1, 2]. API calls 1; tokens 15,115.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### Rutuja Herekar.pdf

Source SHA256: `d3df6990b7d635626abc2fd535b6004928936e7957fe4570836e06a5989775be`. Source pages present: [1, 2, 3]. API calls 2; tokens 56,604.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### S  Abhinav.pdf

Source SHA256: `c96250b351a6bddd658c9fa5d8d4cb15f125ca2f1ea8cfe58217dddd51a9de46`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 41,341.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### S gaotam.pdf

Source SHA256: `b43fe187de287b28770aa800fd36c42713a44c6c78e98013b515e6b613b026db`. Source pages present: [1]. API calls 1; tokens 28,182.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 6.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAI KUMAR CHOWDRY.pdf

Source SHA256: `a6ba77fc7dae40af1c410f7c3e6d523ca104976300f5a1d4340fb97ff8b1c457`. Source pages present: [1]. API calls 2; tokens 35,884.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 2.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAIBABBU.pdf

Source SHA256: `86dbaa747abb49cb690c9a6278a38d2f8b168c824981f34f58ca0064ce5c3ca3`. Source pages present: [1, 2, 3, 4]. API calls 1; tokens 30,210.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 0.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAIPREETHIJUNGA1_3.pdf

Source SHA256: `d3386b4ac4470acdc577cf7d16b2f13a419970b49043a1245f94c44b00461cba`. Source pages present: [1, 2, 3, 4, 5, 6]. API calls 1; tokens 63,693.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 7.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SANDHYABR.pdf

Source SHA256: `9d4a06d6d2d89fa85a44d5992c5f272361ce10ee8bd03aa245de96bc02feb06d`. Source pages present: [1, 2, 3]. API calls 1; tokens 17,744.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-1: multiple_dated_employment_headers_in_one_group Proposed groups: 1.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SANDHYA_KUMAR.pdf

Source SHA256: `367b1def46ca45bf5901b562312724c74b0aef479c7aae24abfb6a191a1776da`. Source pages present: [1, 2]. API calls 1; tokens 19,089.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 4.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 1.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SANTHOSH KUMARK.pdf

Source SHA256: `da7ad81a04a6b1e6fdf711a7716076dcec72e28d4ddc615522d20a2fd34aa2d9`. Source pages present: [1, 2, 3, 4]. API calls 2; tokens 81,401.

Section/source flags: No heuristic flags; this is not proof of correct assignment..

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 9.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SARVAGYA.pdf

Source SHA256: `c5843cc4898b5a7e6170dc210257cce3da7639530be5394dee043b0864c7698c`. Source pages present: [1, 2]. API calls 1; tokens 21,107.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: experience-3: multiple_dated_employment_headers_in_one_group Proposed groups: 3.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 3.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SAYLI_ PACHANEKAR.pdf

Source SHA256: `132ad8ef6d491e49d740d23d1aeba4a81596260286574127071fe120aaca1c21`. Source pages present: [1, 2, 3, 4, 5]. API calls 1; tokens 25,710.

Section/source flags: education_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 1.

Education: education-1: multiple_qualification_mentions_in_one_group_requires_review Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SHAIK FATHIMA  RESUME UPDATED.pdf

Source SHA256: `65a5cbd3cf7392f4c8ff15ee97f155c2d1575b44cbe89a5a4037ed249f85f3d7`. Source pages present: [1]. API calls 2; tokens 24,892.

Section/source flags: employment_relationship_concerns.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No proposed experience groups; original PDF review required Proposed groups: 0.

Education: No additional structural flag; degree/institution/year/grade associations are unverified. Proposed groups: 2.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

### SHAIK RUSUM MOHAMMAD RASOOL.pdf

Source SHA256: `79275dc6172967e3b1591506b17f811564d4cbaaba8598b3cda7e5732fb70343`. Source pages present: [1, 2, 3]. API calls 2; tokens 56,143.

Section/source flags: education_relationship_concerns; provider_review_failed_local_result_retained.

Repeated-passage candidates: 0; independent-parser unmatched terms: 0; word-boundary splits: 0.

Employment: No additional structural flag; employer/title/date/responsibility associations are unverified. Proposed groups: 9.

Education: education-3: numeric_or_grade_only_entry; education-3: date_only_entry_possible_detached_dates; education-4: numeric_or_grade_only_entry; education-4: date_only_entry_possible_detached_dates Proposed groups: 4.

Independent source-backed semantic verification: **not performed**. Original-PDF word accuracy and section/relationship accuracy are not measured. Complete group member source IDs, text, warning lists, token usage and unresolved text/reasons are in report.json.

## Failure patterns and next steps

- education_relationship_concerns: 49 documents flagged.
- employment_relationship_concerns: 27 documents flagged.
- extraction_duplicate_candidates_require_source_check: 3 documents flagged.
- independent_pdf_text_difference_requires_source_check: 6 documents flagged.
- independent_pdf_text_empty_requires_visual_or_ocr_reference: 1 documents flagged.
- out_of_scope_job_requirements: 6 documents flagged.
- provider_review_failed_local_result_retained: 4 documents flagged.
- source_word_split_across_output_blocks: 1 documents flagged.

Priorities: inspect failed provider decisions without relaxing coverage rules; distinguish non-resume requirements from candidate history; fix source-supported employer/date and education/grade grouping in a separately authorized change; verify word splits and PDF text differences; independently approve a source-bound reference set. Do not force unknown text into a category to improve coverage. No production logic was changed for this batch.

## Commands and tests

Exact stage commands and timestamps are in ../manifest.json. All stage scripts are existing batch implementations; run_pilot50_review.py only selects/freezes scope and sequences them. The checkpoint binding gate rejects changed sources, pipeline hashes or provider configuration on resume. No prior-run provider output was imported. This command does not run the regression suite. Refer to separately recorded regression-test results; do not infer that tests ran for this batch.

## Preservation and readiness

Protected pre-existing artifacts checked: 3745; changed: 0. Original PDFs, annotations, gold and all prior reports remain untouched. Only the separate 200-document directory contains new processing artifacts.

**Do not scale further on the basis of assignment coverage.** This run exposes unresolved provider/source/grouping cases; independent semantic accuracy remains unknown. This report covers only the frozen document scope recorded in the manifest.
