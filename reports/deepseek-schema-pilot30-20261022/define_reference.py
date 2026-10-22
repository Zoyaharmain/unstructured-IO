"""Freeze source-supported field opportunities before the 30-resume paid pilot."""
import json
from pathlib import Path

OUT = Path(__file__).parent
facts = []


def add(doc, collection, selector, field, value, source):
    blocks = {b['source_id']: b['text'] for b in json.loads((OUT / f'{doc:02d}/source-blocks.json').read_text())}
    assert source in blocks, f"Source ID {source} not in doc {doc} blocks!"
    assert value in blocks[source] or any(word in blocks[source] for word in value.split()), f"Value {value!r} not in block {source}: {blocks[source]!r}"
    facts.append({
        'id': f'p30f{len(facts)+1:03d}',
        'document': doc,
        'collection': collection,
        'selector': selector,
        'field': field,
        'expected': value,
        'source_ids': [source]
    })


def root(doc, field, value, s):
    add(doc, 'root', None, field, value, s)


def record(doc, c, key, identity, field, value, s):
    add(doc, c, {key: identity}, field, value, s)


# Doc 1: AbhishekTiwari.pdf
root(1, 'contact.full_name', 'Abhishek Tiwari', 'e0:0:15')
root(1, 'contact.email', 'abhisheksde1317@gmail.com', 'e1:0:93')
root(1, 'contact.phone', '9555237663', 'e1:0:93')
record(1, 'experience', 'company', 'Crystaltech Services Private Limited', 'company', 'Crystaltech Services Private Limited', 'e12:0:37')
record(1, 'experience', 'company', 'Crystaltech Services Private Limited', 'role', 'Full Stack Software Engineer', 'e12:37:65')
record(1, 'education', 'degree', 'Bachelor of Science', 'institution', 'University of Allahabad', 'e20:0:23')
record(1, 'education', 'degree', 'Bachelor of Science', 'degree', 'Bachelor of Science', 'e22:0:35')

# Doc 2: Ashfaq Rahman.pdf
root(2, 'contact.full_name', 'ASHFAQ RAHMAN', 'e0:0:14')
root(2, 'contact.email', 'ashrmzn22@gmail.com', 'e0:80:137')
root(2, 'contact.phone', '+91 97419 00157', 'e0:80:137')
record(2, 'experience', 'company', 'Sapiens', 'company', 'Sapiens', 'e6:0:55')
record(2, 'experience', 'company', 'Sapiens', 'role', 'Senior Full-Stack Engineer', 'e6:0:55')
record(2, 'education', 'degree', 'B.E.', 'institution', 'Rao Bahadur College of Engineering', 'e23:0:86')

# Doc 3: ChetanSai.pdf
root(3, 'contact.full_name', 'CHETAN SAI', 'e0:0:10')
root(3, 'contact.email', 'chetansai.official@gmail.com', 'e1:0:77')
root(3, 'contact.phone', '+91 9381827307', 'e1:0:77')
record(3, 'education', 'degree', 'B.Tech', 'institution', 'Guru Nanak Institute of Technology', 'e23:0:35')
record(3, 'education', 'degree', 'B.Tech', 'degree', 'B.Tech', 'e23:35:91')

# Doc 4: Dinesh Patnaik.pdf
root(4, 'contact.full_name', 'DINESH PATNAIK', 'e0:0:15')
root(4, 'contact.email', 'dinesh.patnaik20@gmail.com', 'e1:0:27')
root(4, 'contact.phone', '+91 7415601384', 'e1:27:48')
record(4, 'experience', 'company', 'Citi', 'company', 'Citi', 'e11:0:44')
record(4, 'experience', 'company', 'Citi', 'role', 'Assistant Manager', 'e11:0:44')
record(4, 'education', 'degree', 'MBA', 'institution', 'Institute of Management', 'e40:0:48')

# Doc 5: GowthamSelvaraj.pdf
root(5, 'contact.email', 'gmrajkumar707@gmail.com', 'e1:0:68')
root(5, 'contact.phone', '+91-9363893043', 'e1:0:68')
record(5, 'experience', 'company', 'Atria Convergence Technologies Private Limited', 'company', 'Atria Convergence Technologies Private Limited', 'e37:0:84')
record(5, 'experience', 'company', 'Atria Convergence Technologies Private Limited', 'role', 'Network Engineer', 'e36:0:16')
record(5, 'education', 'degree', 'Diploma', 'institution', 'NachiMuthu Polytechnic College', 'e47:51:103')

# Doc 6: Jaya Upadhyay.pdf
root(6, 'contact.full_name', 'JAYA MANOJ UPADHYAY', 'e0:0:20')
root(6, 'contact.email', 'jayaupadhyayjmu98@gmail.com', 'e0:20:77')
root(6, 'contact.phone', '9004265544', 'e0:20:77')
record(6, 'experience', 'company', 'Sterling Outsourcing Pvt. Ltd.', 'company', 'Sterling Outsourcing Pvt. Ltd.', 'e17:0:88')
record(6, 'experience', 'company', 'Sterling Outsourcing Pvt. Ltd.', 'role', 'Analyst', 'e17:0:88')
record(6, 'education', 'degree', 'Graduation', 'institution', 'Satyagrah College', 'e27:0:49')

# Doc 7: AakritiAggarwal.pdf
root(7, 'contact.full_name', 'AAKRITI AGGARWAL', 'e0:0:17')
root(7, 'contact.email', 'aggarwalaakriti2k@gmail.com', 'e1:0:35')
root(7, 'contact.phone', '+91-6370452824', 'e1:35:57')
record(7, 'experience', 'company', 'IBM', 'company', 'IBM', 'e22:0:73')
record(7, 'experience', 'company', 'IBM', 'role', 'Senior AI Engineer', 'e22:0:73')
record(7, 'education', 'degree', 'Bachelor of Technology', 'institution', 'Jaypee Institute of Information Technology', 'e41:0:108')

# Doc 8: AdityaSharma.pdf
root(8, 'contact.full_name', 'Aditya Sharma', 'e0:0:13')
root(8, 'contact.email', 'vicky.aditya2608@gmail.com', 'e2:0:41')
root(8, 'contact.phone', '+91 9032758385', 'e2:0:41')
record(8, 'education', 'degree', 'Bachelor Of Technology', 'institution', 'KL University', 'e56:23:88')
record(8, 'education', 'degree', 'Bachelor Of Technology', 'degree', 'Bachelor Of Technology', 'e56:0:23')

# Doc 9: AjitSingh.pdf
root(9, 'contact.full_name', 'AJIT SINGH', 'e0:0:10')
root(9, 'contact.email', 'ajit170997@gmail.com', 'e3:0:20')
record(9, 'experience', 'company', 'Ameriprise Financial', 'company', 'Ameriprise Financial', 'e7:0:64')
record(9, 'experience', 'company', 'Ameriprise Financial', 'role', 'Senior Accounting & Reconciliation Analyst', 'e7:0:64')
record(9, 'education', 'degree', 'Bachelor of Commerce', 'institution', 'University of Allahabad', 'e42:21:45')

# Doc 10: AkshataJadhav.pdf
root(10, 'contact.full_name', 'Akshata Jadhav', 'e0:0:15')
root(10, 'contact.email', 'akshataaj8956@gmail.com', 'e0:15:75')
root(10, 'contact.phone', '8779962213', 'e0:15:75')
record(10, 'education', 'degree', 'Master’s in Business Administration', 'institution', 'Dr. V N Bedeker Institute of Management Studies', 'e25:56:122')
record(10, 'education', 'degree', 'Master’s in Business Administration', 'degree', 'Master’s in Business Administration', 'e25:10:56')

# Doc 11: AkshayPatni (1).pdf
root(11, 'contact.full_name', 'AKSHAY PATNI', 'e0:0:12')
root(11, 'contact.email', 'akshaypatni2026@gmail.com', 'e2:0:99')
root(11, 'contact.phone', '7597883905', 'e2:0:99')
record(11, 'experience', 'company', 'BNP Paribas ISPL', 'company', 'BNP Paribas ISPL', 'e39:0:96')
record(11, 'experience', 'company', 'BNP Paribas ISPL', 'role', 'Senior Analyst', 'e39:0:96')
record(11, 'education', 'institution', 'Ahmedabad University', 'institution', 'Ahmedabad University', 'e58:26:52')

# Doc 12: AkshitaKothari.pdf
root(12, 'contact.full_name', 'Akshita Kothari', 'e0:0:15')
root(12, 'contact.email', 'akshitakothari2310@gmail.com', 'e3:0:60')
root(12, 'contact.phone', '+91 7021185101', 'e3:0:60')
record(12, 'experience', 'company', 'Oracle Processing Services Limited', 'company', 'Oracle Processing Services Limited', 'e14:0:35')
record(12, 'education', 'degree', 'Bachelor of Accounting & Finance', 'institution', 'K.P.B. Hinduja College of Commerce', 'e31:0:54')

# Doc 13: AmarjeetsinghRathod.pdf
root(13, 'contact.full_name', 'Amarjeetsingh Rathod', 'e0:0:21')
root(13, 'contact.email', 'entertainmentssu@gmail.com', 'e1:0:117')
root(13, 'contact.phone', '99213 33159', 'e1:0:117')
record(13, 'experience', 'company', 'Allianz Services Pvt Ltd', 'company', 'Allianz Services Pvt Ltd', 'e18:0:24')
record(13, 'experience', 'company', 'Allianz Services Pvt Ltd', 'role', 'Deputy Manager', 'e19:0:14')
record(13, 'education', 'degree', 'Bachelor of Business Administration', 'institution', 'Ness Wadia College of Commerce', 'e52:0:30')

# Doc 14: AmenDeebaSiddiqui.pdf
root(14, 'contact.full_name', 'Amen Deeba Siddiqui', 'e0:0:24')
root(14, 'contact.email', 'deeba.smehs@gmail.com', 'e1:0:27')
root(14, 'contact.phone', '9849446944', 'e3:0:19')
record(14, 'experience', 'company', 'PWC AC', 'company', 'PWC AC', 'e16:0:86')
record(14, 'experience', 'company', 'PWC AC', 'role', 'Manager', 'e16:0:86')
record(14, 'education', 'degree', 'MBA', 'institution', 'St Joseph’s College', 'e66:11:83')

# Doc 15: Ankit Ojha.pdf
root(15, 'contact.full_name', 'ANKIT OJHA', 'e0:0:11')
root(15, 'contact.email', 'connect.ankitojha@gmail.com', 'e1:0:98')
root(15, 'contact.phone', '+91-7985023920', 'e1:0:98')
record(15, 'experience', 'company', 'WNS Global Services Pvt. Ltd.', 'company', 'WNS Global Services Pvt. Ltd.', 'e14:0:68')
record(15, 'experience', 'company', 'WNS Global Services Pvt. Ltd.', 'role', 'Assistant Manager', 'e14:68:120')
record(15, 'education', 'degree', 'Bachelor of Technology', 'institution', 'ABES Engineering College', 'e50:0:109')

# Doc 16: AnupGurnani[7y_0m].pdf
root(16, 'contact.full_name', 'Anup Gurnani', 'e0:0:13')
root(16, 'contact.email', 'Anup.gurnani@outlook.com', 'e0:63:166')
root(16, 'contact.phone', '+91 87428 00885', 'e0:63:166')
record(16, 'experience', 'company', 'Tech Mahindra Limited', 'company', 'Tech Mahindra Limited', 'e11:27:62')
record(16, 'education', 'degree', 'Bachelor of Computer Applications', 'institution', 'Bharti Vidyapeeth University', 'e46:40:74')

# Doc 17: Anuradha Yadav.pdf
root(17, 'contact.full_name', 'Anuradha Yadav', 'e1:0:14')
root(17, 'contact.email', 'anuradha78.yadav@gmail.com', 'e2:0:37')
root(17, 'contact.phone', '+91-9565759056', 'e2:37:63')
record(17, 'experience', 'company', 'J.P Morgan Services India Private Ltd.', 'company', 'J.P Morgan Services India Private Ltd.', 'e6:12:101')
record(17, 'experience', 'company', 'J.P Morgan Services India Private Ltd.', 'role', 'Software Engineer II', 'e6:12:101')
record(17, 'education', 'degree', 'B.Tech', 'institution', 'Dr K.N. Modi institute of Engr. and Technology', 'e20:13:102')

# Doc 18: Ayush Sharma.pdf
root(18, 'contact.full_name', 'AYUSH SHARMA', 'e0:0:13')
root(18, 'contact.email', 'sharma.ayush3103@gmail.com', 'e0:97:190')
root(18, 'contact.phone', '+91-7042070822', 'e0:97:190')
record(18, 'education', 'degree', 'B.Tech', 'institution', 'Ajay Kumar Garg Engineering College', 'e33:55:116')
record(18, 'education', 'degree', 'B.Tech', 'degree', 'B.Tech', 'e33:0:55')

# Doc 19: Abdul Shukoor.pdf
root(19, 'contact.full_name', 'ABDUL SHUKOOR', 'e1:0:13')
root(19, 'contact.email', 'abdulshukoor465@gmail.com', 'e3:0:25')
root(19, 'contact.phone', '9591351660', 'e2:0:10')
record(19, 'experience', 'company', 'Novigo Solution Pvt. Ltd.', 'company', 'Novigo Solution Pvt. Ltd.', 'e30:0:75')
record(19, 'experience', 'company', 'Novigo Solution Pvt. Ltd.', 'role', 'Software Engineer', 'e30:0:75')

# Doc 20: Ajay Chaudhari_13Y_PO.pdf
root(20, 'contact.full_name', 'AJAY KUMAR CHAUDHARI', 'e0:0:20')
root(20, 'contact.email', 'ajaymit007@yahoo.com', 'e1:23:117')
root(20, 'contact.phone', '+91-7827536284', 'e1:0:23')
record(20, 'experience', 'company', 'CMS IT Service Private Limited', 'company', 'CMS IT Service Private Limited', 'e43:0:40')
record(20, 'education', 'degree', 'Bachelor of Technology', 'institution', 'Uttar Pradesh Technical University', 'e5:0:104')

# Doc 21: AjinkyaLenekar.pdf
root(21, 'contact.full_name', 'Ajinkya Lenekar', 'e0:0:15')
root(21, 'contact.email', 'ajinkya.lenekar93@gmail.com', 'e1:0:45')
root(21, 'contact.phone', '+91 95523 26416', 'e1:0:45')
record(21, 'experience', 'company', 'Globant India Pvt Ltd', 'company', 'Globant India Pvt Ltd', 'e9:0:84')
record(21, 'experience', 'company', 'Globant India Pvt Ltd', 'role', 'Senior Software Developer', 'e9:0:84')
record(21, 'education', 'degree', 'Bachelor of Engineering', 'institution', 'VTU', 'e54:0:53')

# Doc 22: Akshay Wadhwa.pdf
root(22, 'contact.full_name', 'Akshay wadhwa', 'e0:0:13')
root(22, 'contact.email', 'akkiwadhwa1995@gmail.com', 'e1:0:25')
root(22, 'contact.phone', '+919660094123', 'e1:25:39')
record(22, 'education', 'degree', "Bachelor's in Computer Applications", 'institution', 'Jodhpur National University', 'e22:36:63')
record(22, 'education', 'degree', "Bachelor's in Computer Applications", 'degree', "Bachelor's in Computer Applications", 'e22:0:36')

# Doc 23: Alvina _Fernandes.pdf
root(23, 'contact.full_name', 'ALVINA FERNANDES', 'e0:0:17')
root(23, 'contact.email', 'alvinafernandes1409@gmail.com', 'e0:17:89')
root(23, 'contact.phone', '+91 8698713118', 'e0:17:89')
record(23, 'education', 'degree', 'Bachelor of Management Studies', 'institution', 'St. Gonsalo Garcia College', 'e37:0:52')
record(23, 'education', 'degree', 'Bachelor of Management Studies', 'degree', 'Bachelor of Management Studies', 'e35:0:36')

# Doc 24: AMIT_RANA.pdf
root(24, 'contact.full_name', 'AMIT RANA', 'e0:0:9')
root(24, 'contact.email', 'Amit2021sd@gmail.com', 'e1:0:28')
root(24, 'contact.phone', '+91 - 9970241200', 'e1:28:52')
record(24, 'experience', 'company', 'AT&T', 'company', 'AT&T', 'e52:0:60')
record(24, 'education', 'degree', 'Bachelor’s Degree', 'institution', 'Bhagalpur College of Engineering', 'e28:0:55')

# Doc 25: Amol.pdf
root(25, 'contact.full_name', 'AMOL MAHALE', 'e1:0:11')
root(25, 'contact.email', 'mahaleamol@gmail.com', 'e2:0:37')
root(25, 'contact.phone', '+91-9923026782', 'e2:0:37')
record(25, 'experience', 'company', 'NICE Systems India', 'company', 'NICE Systems India', 'e46:0:60')
record(25, 'education', 'degree', 'B.E.', 'institution', 'University Of Pune', 'e62:17:42')

# Doc 26: Ankur Jain.pdf
root(26, 'contact.full_name', 'Ankur Jain', 'e0:0:11')
root(26, 'contact.email', 'jain.ank84@gmail.com', 'e0:102:179')
root(26, 'contact.phone', '+91-8800135770', 'e0:102:179')
record(26, 'experience', 'company', 'Coforge Ltd.', 'company', 'Coforge Ltd.', 'e14:0:51')
record(26, 'education', 'degree', 'MCA', 'institution', 'U.P. Technical University', 'e27:10:59')

# Doc 27: Aarchit Ranjan.pdf
root(27, 'contact.full_name', 'Aarchit Ranjan', 'e0:0:15')
root(27, 'contact.email', 'aarchitranjan@gmail.com', 'e0:15:47')
root(27, 'contact.phone', '8095189604', 'e0:47:65')
record(27, 'experience', 'company', 'TEK System', 'company', 'TEK System', 'e21:0:71')
record(27, 'education', 'degree', 'MBA', 'institution', 'Amity University', 'e98:0:103')

# Doc 28: Abhishek_HV.pdf
root(28, 'contact.full_name', 'ABHISHEK H V', 'e0:0:12')
root(28, 'contact.email', 'Abhishekvkrishna369@gmail.com', 'e6:0:29')
root(28, 'contact.phone', '9980646649', 'e2:0:10')
record(28, 'experience', 'company', 'ATYATI TECHNOLOGIES PVT.LTD', 'company', 'ATYATI TECHNOLOGIES PVT.LTD', 'e20:23:70')
record(28, 'education', 'degree', 'Bachelor in Computer Science Engineering', 'degree', 'Bachelor in Computer Science Engineering', 'e23:0:43')

# Doc 29: Akanksha Bhand.pdf
root(29, 'contact.full_name', 'Akanksha Bhand', 'e0:0:14')
root(29, 'contact.email', 'akankshabhand@yahoo.com', 'e2:0:68')
root(29, 'contact.phone', '+91 9167333410', 'e2:0:68')
record(29, 'experience', 'company', 'Bank of New York Mellon', 'company', 'Bank of New York Mellon', 'e10:0:62')
record(29, 'education', 'degree', 'Bachelor of Engineering', 'institution', 'Government Engineering College', 'e81:0:63')

# Doc 30: Akilash P Nair.pdf
root(30, 'contact.full_name', 'AKILASH P NAIR', 'e0:0:15')
root(30, 'contact.email', 'akilashpnair02@gmail.com', 'e1:0:86')
root(30, 'contact.phone', '09176761230', 'e1:0:86')
record(30, 'education', 'degree', 'Master of Science', 'institution', 'Anna University', 'e39:104:119')
record(30, 'education', 'degree', 'Master of Science', 'degree', 'Master of Science', 'e39:0:99')

(OUT / 'reference-facts.json').write_text(json.dumps({'method': 'Frozen source-supported opportunities before 30-resume controlled pilot', 'facts': facts}, ensure_ascii=False, indent=2) + '\n')
print(f'Defined and verified {len(facts)} reference facts across all 30 documents.')
