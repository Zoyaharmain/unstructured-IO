"""Freeze source-supported field opportunities before the 10-resume paid pilot."""
import json
from pathlib import Path

OUT = Path(__file__).parent
facts = []


def add(doc, collection, selector, field, value, source):
    blocks = {b['source_id']: b['text'] for b in json.loads((OUT / f'{doc:02d}/source-blocks.json').read_text())}
    assert source in blocks, f"Source ID {source} not in doc {doc} blocks!"
    facts.append({
        'id': f'p10f{len(facts)+1:03d}',
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


# Doc 1: KARTHIYAYINI S_1.pdf (Dense 4-page banking operations resume)
root(1, 'contact.full_name', 'KARTHIYAYINI. S', 'e0:0:15')
root(1, 'contact.email', 'Karthiyayini0208@gmail.com', 'e1:0:34')
root(1, 'contact.phone', '+91 9500115159', 'e2:0:21')
root(1, 'total_experience_years', 11, 'e7:0:33')
for company, role, s in [
    ('Barclays Global Service Centre Private Limited', 'Senior Associate', 'e8:0:80'),
    ('BNY Mellon (I) International Operations', 'Senior Analyst', 'e36:0:72'),
    ('Microsoft (I) Pvt. Ltd.', 'Front Office Executive', 'e73:0:63')
]:
    record(1, 'experience', 'company', company, 'company', company, s)
    record(1, 'experience', 'company', company, 'role', role, s)
for field, value, s in [
    ('degree', 'MBA', 'e87:0:22'),
    ('institution', 'SRM University', 'e87:0:22'),
    ('start_year', '2014', 'e87:22:57'),
    ('graduation_year', '2016', 'e87:22:57'),
    ('grade_or_gpa', '8.9', 'e87:22:57')
]:
    record(1, 'education', 'degree', 'MBA', field, value, s)
for field, value in [
    ('degree', 'BCA'),
    ('field_of_study', 'Computer Applications'),
    ('institution', 'University of Madras'),
    ('graduation_year', '2014')
]:
    record(1, 'education', 'degree', 'BCA', field, value, 'e92:0:84')

# Doc 2: A Lokhande.pdf (2-page Java developer resume)
root(2, 'contact.email', 'ashish.lokhande147@gmail.com', 'e7:0:30')
root(2, 'contact.phone', '+91 8421279582', 'e8:0:30')
root(2, 'professional_title', 'Senior Java Developer', 'e1:13:34')
root(2, 'total_experience_years', 6, 'e2:0:107')
for company, role, cs, rs in [
    ('Capgemini', 'Senior Java Consultant', 'e12:0:9', 'e11:0:22'),
    ('Cognizant', 'Java Developer', 'e20:0:10', 'e19:0:14'),
    ('Aurus Inc', 'Java Developer', 'e28:0:10', 'e27:0:14')
]:
    record(2, 'experience', 'company', company, 'company', company, cs)
    record(2, 'experience', 'company', company, 'role', role, rs)
record(2, 'education', 'degree', "Bachelor's degree", 'degree', "Bachelor's degree", 'e37:0:17')
record(2, 'education', 'degree', "Bachelor's degree", 'field_of_study', 'Engineering', 'e38:0:11')

# Doc 3: Abhishek Barnwa.pdf (1-page ServiceNow technical resume)
root(3, 'contact.full_name', 'Abhishek Barnwal', 'e0:0:16')
root(3, 'contact.email', 'tech.abhishek.barnwal@gmail.com', 'e1:21:141')
root(3, 'contact.phone', '+91 7004885397', 'e1:21:141')
root(3, 'professional_title', 'ServiceNow Developer', 'e1:0:21')
root(3, 'total_experience_years', 4, 'e3:0:118')
for field, value, s in [
    ('company', 'Virtusa Pvt. Ltd.', 'e4:0:18'),
    ('start_date', 'May 2022', 'e5:0:19'),
    ('end_date', 'Present', 'e5:0:19')
]:
    record(3, 'experience', 'company', 'Virtusa', field, value, s)
for field, value, s in [
    ('degree', 'B.Tech', 'e28:30:67'),
    ('field_of_study', 'Computer Science', 'e28:30:67'),
    ('institution', 'Techno Main Salt Lake College', 'e28:0:30'),
    ('grade_or_gpa', '8.9', 'e28:30:67'),
    ('graduation_year', '2022', 'e29:0:12')
]:
    record(3, 'education', 'degree', 'B.Tech', field, value, s)

# Doc 4: A Suribhotla.pdf (4-page data analytics resume)
root(4, 'contact.full_name', 'A Suribhotla', 'e0:0:12')
root(4, 'contact.email', 'abhisheksuribhotla@gmail.com', 'e2:27:63')
root(4, 'contact.phone', '+91 8790553327', 'e2:63:84')
root(4, 'professional_title', 'Senior Data Expert – Data Analyst & Data Modeler', 'e1:0:48')
for company, start, end, cs, ds in [
    ('Virtusa Consulting Services', 'Jan 2022', 'Present', 'e34:0:40', 'e34:74:92'),
    ('Keolis Hyderabad Mass Rapid Transit System Ltd', 'Dec 2017', 'Jan 2022', 'e60:0:59', 'e60:90:109'),
    ('Concentrix', 'Apr 2017', 'Nov 2017', 'e77:0:27', 'e77:54:73')
]:
    for field, value, s in [('company', company, cs), ('start_date', start, ds), ('end_date', end, ds)]:
        record(4, 'experience', 'company', company, field, value, s)
for field, value, s in [
    ('degree', 'Bachelor of Technology', 'e87:0:65'),
    ('field_of_study', 'Electronics & Communication Engineering', 'e87:0:65'),
    ('institution', 'Raghu Engineering College', 'e87:65:107'),
    ('graduation_year', '2016', 'e87:107:126')
]:
    record(4, 'education', 'degree', 'Bachelor of Technology', field, value, s)

# Doc 5: AswathyRajagopal.pdf (2-page regulatory QA resume)
root(5, 'contact.full_name', 'ASWATHY R', 'e0:0:10')
root(5, 'contact.email', 'aswathyr1694@gmail.com', 'e0:10:68')
root(5, 'contact.phone', '+91 7026754548', 'e0:10:68')
root(5, 'total_experience_years', 8, 'e2:0:134')
for company, role, s in [
    ('Standard Chartered Global Business Services', 'Manager, Non-Financial Regulatory Reporting', 'e15:0:110'),
    ('Deutsche Bank', 'Associate, SFTR Regulatory Reporting', 'e22:0:92'),
    ('J.P. Morgan', 'Senior Analyst, Client Reporting', 'e36:0:87'),
    ('State Street Syntel', 'Analyst', 'e44:0:65')
]:
    record(5, 'experience', 'company', company, 'company', company, s)
    record(5, 'experience', 'company', company, 'role', role, s)
for degree, college, year, s in [
    ('PGDM', 'Balaji Institute of Modern Management', '2017', 'e58:0:63'),
    ('B.com', 'M.E.S College', '2015', 'e59:0:40')
]:
    for field, value in [('degree', degree), ('institution', college), ('graduation_year', year)]:
        record(5, 'education', 'degree', degree, field, value, s)

# Doc 6: Manisha Singh.pdf (1-page software engineer resume)
root(6, 'contact.full_name', 'MANISHA SINGH', 'e0:0:13')
root(6, 'contact.email', 'manishasinghm2101@gmail.com', 'e1:34:75')
root(6, 'contact.phone', '9004425195', 'e1:75:85')
for company, role, cs, rs in [
    ('Tata Starbucks Pvt Ltd', 'Barista Trainer', 'e5:0:39', 'e5:0:39'),
    ('FirstSource', 'Customer support agent', 'e11:0:35', 'e11:0:35')
]:
    record(6, 'experience', 'company', company, 'company', company, cs)
    record(6, 'experience', 'company', company, 'role', role, rs)
for field, value, s in [
    ('degree', 'B.Com (Bachelor of Commerce)', 'e19:0:28'),
    ('institution', 'Tolani College of Commerce', 'e18:10:36'),
    ('graduation_year', '2022', 'e20:0:17')
]:
    record(6, 'education', 'degree', 'B.Com', field, value, s)

# Doc 7: MADHUSUDHANHK.pdf (2-page IT infrastructure engineer resume)
root(7, 'contact.email', 'Madhusudhan.Mskj@gmail.com', 'e4:0:34')
root(7, 'contact.phone', '9686364439', 'e5:0:19')
root(7, 'total_experience_years', 5, 'e1:0:29')
for company, role, s in [
    ('NIELSEN', 'SERVICENOW DEVELOPER', 'e6:25:88'),
    ('TECHMAHINDRA', 'SERVICENOW DEVELOPER', 'e24:0:62')
]:
    record(7, 'experience', 'company', company, 'company', company, s)
    record(7, 'experience', 'company', company, 'role', role, s)

# Doc 8: RAMU AKKENAPALLY.pdf (2-page database administrator resume)
root(8, 'contact.full_name', 'RAMU AKKENAPALLY', 'e0:0:16')
root(8, 'contact.email', 'rakkena.pally36@gmail.com', 'e1:0:62')
root(8, 'contact.phone', '+91- 9989306517', 'e1:0:62')
root(8, 'total_experience_years', 17, 'e3:0:86')
for company, role, s in [
    ('AVAYA India Pvt. Ltd', 'Principal Technical Support Engineer', 'e20:0:89'),
    ('HCL Infosystems', 'Senior Engineer – Service Delivery', 'e24:0:79'),
    ('Wipro 3D Networks', 'Customer Service Engineer', 'e24:79:149')
]:
    record(8, 'experience', 'company', company, 'company', company, s)
    record(8, 'experience', 'company', company, 'role', role, s)
for field, value, s in [
    ('degree', 'Masters in Telecommunication & Software Engineering', 'e30:0:79'),
    ('institution', 'BITS Pilani (WILP)', 'e30:0:79'),
    ('graduation_year', '2016', 'e30:0:79')
]:
    record(8, 'education', 'degree', 'Masters in Telecommunication', field, value, s)
for field, value, s in [
    ('degree', 'M.Sc (Computer Science)', 'e30:82:133'),
    ('institution', 'Osmania University', 'e30:82:133'),
    ('graduation_year', '2004', 'e30:82:133')
]:
    record(8, 'education', 'degree', 'M.Sc', field, value, s)

# Doc 9: Aparna_Bharti.pdf (3-page business analyst resume)
root(9, 'contact.full_name', 'Aparna Bharti', 'e0:0:14')
root(9, 'contact.email', 'aparnabhrt@gmail.com', 'e0:62:127')
root(9, 'contact.phone', '+91 9753285271', 'e0:62:127')
root(9, 'professional_title', 'Data Governance & Regulatory Compliance Analyst', 'e0:14:62')
root(9, 'total_experience_years', 6, 'e2:0:128')
for company, role, s in [
    ('Global Pantry Grocery', 'Data Governance Analyst', 'e12:0:67'),
    ('S&P Global Inc.', 'Data Analyst', 'e24:0:50'),
    ('Acadecraft Pvt. Ltd.', 'Quality Analyst', 'e36:0:54'),
    ('Prime Research Pvt. Ltd.', 'Research Analyst', 'e49:0:71')
]:
    record(9, 'experience', 'company', company, 'company', company, s)
    record(9, 'experience', 'company', company, 'role', role, s)
for field, value, s in [
    ('degree', 'MBA in Finance and Marketing', 'e52:0:66'),
    ('institution', 'Amity University, Noida', 'e52:0:66'),
    ('graduation_year', '2021', 'e52:0:66')
]:
    record(9, 'education', 'degree', 'MBA', field, value, s)
for field, value, s in [
    ('degree', 'BBA in Financial Services and Marketing', 'e52:66:174'),
    ('institution', 'University of Petroleum and Energy Studies', 'e52:66:174'),
    ('graduation_year', '2018', 'e52:66:174')
]:
    record(9, 'education', 'degree', 'BBA', field, value, s)

# Doc 10: G S Sandhya Rani.pdf (4-page QA lead resume)
root(10, 'contact.full_name', 'G S Sandhya Rani', 'e0:0:16')
root(10, 'contact.email', 'gs.sandhya7@gmail.com', 'e1:20:48')
root(10, 'contact.phone', '+91 7760458117', 'e1:0:20')
root(10, 'total_experience_years', 11.8, 'e6:0:97')
for company, role, s in [
    ('Tata Consultancy Services', 'IT Analyst', 'e57:0:38'),
    ('Wipro Technologies Ltd', 'Senior Project Engineer', 'e69:0:48')
]:
    record(10, 'experience', 'company', company, 'company', company, s)
    record(10, 'experience', 'company', company, 'role', role, s)
for field, value, s in [
    ('degree', 'B.Sc Computers Science', 'e25:0:85'),
    ('institution', 'S.S.G.S Degree College, Guntakal', 'e25:0:85'),
    ('graduation_year', '2011', 'e25:0:85')
]:
    record(10, 'education', 'degree', 'B.Sc', field, value, s)
for field, value, s in [
    ('degree', 'Master of Software Engineering', 'e26:0:76'),
    ('institution', 'BITS, Pilani', 'e26:0:76'),
    ('graduation_year', '2015', 'e26:0:76')
]:
    record(10, 'education', 'degree', 'Master of Software Engineering', field, value, s)

(OUT / 'reference-facts.json').write_text(json.dumps({
    'method': 'AI analyst source-block opportunities frozen before pilot; validated against original PDFs',
    'facts': facts,
    'total_facts': len(facts)
}, ensure_ascii=False, indent=2) + '\n')

print(f'Frozen 10-resume pilot reference field opportunities: {len(facts)}')

