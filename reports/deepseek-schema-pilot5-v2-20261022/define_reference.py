"""Freeze source-supported field opportunities before the second paid pilot."""
import json
from pathlib import Path
OUT=Path(__file__).parent;facts=[]
def add(doc,collection,selector,field,value,source):
 blocks={b['source_id']:b['text'] for b in json.loads((OUT/f'{doc:02d}/source-blocks.json').read_text())}
 assert source in blocks
 facts.append({'id':f'v2f{len(facts)+1:03d}','document':doc,'collection':collection,'selector':selector,'field':field,'expected':value,'source_ids':[source]})
def root(doc,field,value,s):add(doc,'root',None,field,value,s)
def record(doc,c,key,identity,field,value,s):add(doc,c,{key:identity},field,value,s)
root(1,'contact.email','ashish.lokhande147@gmail.com','e7:0:30');root(1,'contact.phone','+91 8421279582','e8:0:30');root(1,'professional_title','Senior Java Developer','e1:13:34');root(1,'total_experience_years',6,'e2:0:107')
for company,role,cs,rs in [('Capgemini','Senior Java Consultant','e12:0:9','e11:0:22'),('Cognizant','Java Developer','e20:0:10','e19:0:14'),('Aurus Inc','Java Developer','e28:0:10','e27:0:14')]:
 record(1,'experience','company',company,'company',company,cs);record(1,'experience','company',company,'role',role,rs)
record(1,'education','degree',"Bachelor's degree",'degree',"Bachelor's degree",'e37:0:17');record(1,'education','degree',"Bachelor's degree",'field_of_study','Engineering','e38:0:11')
root(2,'contact.full_name','Abhishek Barnwal','e0:0:16');root(2,'contact.email','tech.abhishek.barnwal@gmail.com','e1:21:141');root(2,'contact.phone','+91 7004885397','e1:21:141');root(2,'professional_title','ServiceNow Developer','e1:0:21');root(2,'total_experience_years',4,'e3:0:118')
for field,value,s in [('company','Virtusa Pvt. Ltd.','e4:0:18'),('start_date','May 2022','e5:0:19'),('end_date','Present','e5:0:19')]:record(2,'experience','company','Virtusa',field,value,s)
for field,value,s in [('degree','B.Tech','e28:30:67'),('field_of_study','Computer Science','e28:30:67'),('institution','Techno Main Salt Lake College','e28:0:30'),('grade_or_gpa','8.9','e28:30:67'),('graduation_year','2022','e29:0:12')]:record(2,'education','degree','B.Tech',field,value,s)
root(3,'contact.full_name','A Suribhotla','e0:0:12');root(3,'contact.email','abhisheksuribhotla@gmail.com','e2:27:63');root(3,'contact.phone','+91 8790553327','e2:63:84');root(3,'professional_title','Senior Data Expert – Data Analyst & Data Modeler','e1:0:48')
for company,start,end,cs,ds in [('Virtusa Consulting Services','Jan 2022','Present','e34:0:40','e34:74:92'),('Keolis Hyderabad Mass Rapid Transit System Ltd','Dec 2017','Jan 2022','e60:0:59','e60:90:109'),('Concentrix','Apr 2017','Nov 2017','e77:0:27','e77:54:73')]:
 for field,value,s in [('company',company,cs),('start_date',start,ds),('end_date',end,ds)]:record(3,'experience','company',company,field,value,s)
for field,value,s in [('degree','Bachelor of Technology','e87:0:65'),('field_of_study','Electronics & Communication Engineering','e87:0:65'),('institution','Raghu Engineering College','e87:65:107'),('graduation_year','2016','e87:107:126')]:record(3,'education','degree','Bachelor of Technology',field,value,s)
root(4,'contact.full_name','KARTHIYAYINI. S','e0:0:15');root(4,'contact.email','Karthiyayini0208@gmail.com','e1:0:34');root(4,'contact.phone','+91 9500115159','e2:0:21');root(4,'total_experience_years',11,'e7:0:33')
for company,role,s in [('Barclays Global Service Centre Private Limited','Senior Associate','e8:0:80'),('BNY Mellon (I) International Operations','Senior Analyst','e36:0:72'),('Microsoft (I) Pvt. Ltd.','Front Office Executive','e73:0:63')]:
 record(4,'experience','company',company,'company',company,s);record(4,'experience','company',company,'role',role,s)
for field,value,s in [('degree','MBA','e87:0:22'),('institution','SRM University','e87:0:22'),('start_year','2014','e87:22:57'),('graduation_year','2016','e87:22:57'),('grade_or_gpa','8.9','e87:22:57')]:record(4,'education','degree','MBA',field,value,s)
for field,value in [('degree','BCA'),('field_of_study','Computer Applications'),('institution','University of Madras'),('graduation_year','2014')]:record(4,'education','degree','BCA',field,value,'e92:0:84')
root(5,'contact.full_name','ASWATHY R','e0:0:10');root(5,'contact.email','aswathyr1694@gmail.com','e0:10:68');root(5,'contact.phone','+91 7026754548','e0:10:68');root(5,'total_experience_years',8,'e2:0:134')
for company,role,s in [('Standard Chartered Global Business Services','Manager, Non-Financial Regulatory Reporting','e15:0:110'),('Deutsche Bank','Associate, SFTR Regulatory Reporting','e22:0:92'),('J.P. Morgan','Senior Analyst, Client Reporting','e36:0:87'),('State Street Syntel','Analyst','e44:0:65')]:
 record(5,'experience','company',company,'company',company,s);record(5,'experience','company',company,'role',role,s)
for degree,college,year,s in [('PGDM','Balaji Institute of Modern Management','2017','e58:0:63'),('B.com','M.E.S College','2015','e59:0:40')]:
 for field,value in [('degree',degree),('institution',college),('graduation_year',year)]:record(5,'education','degree',degree,field,value,s)
(OUT/'reference-facts.json').write_text(json.dumps({'method':'AI analyst source-block opportunities frozen before pilot; not PDF/human verified','facts':facts,'limits':'Not exhaustive full-schema recall; garbled identity/date associations excluded where unclear.'},ensure_ascii=False,indent=2)+'\n')
print('Frozen second-pilot field opportunities:',len(facts))
