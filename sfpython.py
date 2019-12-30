import PyPDF2
import json
import os
import os.path
from PyPDF2 import PdfFileReader
from simple_salesforce import Salesforce, SFType, SalesforceLogin
import requests
import glob 


def main():
    # manipulate the session instance (optional)
    sf = Salesforce(username='sampath-2cdm@force.com', password='Oct@2019', security_token='uu9oMKpNGlwfGVOb6OFd4tIjd')
    sessionId = sf.session_id
    instance = sf.sf_instance
    print ('sessionId: ' + sessionId)
    searchkewwords = [];
    sfkeyword = sf.query("SELECT DeveloperName,Id,Keyword__c,Label,Language,MasterLabel,NamespacePrefix,QualifiedApiName FROM SearchKeyword__mdt")
    for r in sfkeyword["records"]:
        searchkewwords.append(r["Keyword__c"])
    print(searchkewwords)
    searchkewwordslen = len(searchkewwords)
    print (searchkewwordslen)

    
    ParentRecordId = "001B000001AY9BJIA1"
    condocsids=[];
    print(ParentRecordId)

    # SELECT ContentDocumentId,Id,LinkedEntityId,ShareType,Visibility FROM ContentDocumentLink WHERE LinkedEntityId = '001B000001AY9BJIA1'
    condoc_query_string = "SELECT ContentDocumentId,Id,LinkedEntityId,ShareType,Visibility FROM ContentDocumentLink WHERE LinkedEntityId="+"'"+ParentRecordId+"'"
    sfcondocs = sf.query(condoc_query_string)
    for r in sfcondocs["records"]:
        condocsids.append(r["ContentDocumentId"])
    
    # convery the list into SOQL Query format
    listidstr=""
    for s in condocsids: 
        if listidstr=="": 
            listidstr += "("+"'"+s+"'"+"," 
        else:
             listidstr += "'"+s+"'"+"," 
    
    finallistidstr = listidstr[:-1]
    finalcondocsids = finallistidstr+")"
    print(finalcondocsids)

    # query_string = "SELECT CreatedDate,ContentDocumentId,ContentLocation,FileExtension,FileType,Id,Title,VersionData FROM ContentVersion where FileExtension='pdf' and ContentDocumentId IN ('069B0000006wEFoIAM','069B0000006wEFtIAM','069B0000006wEFyIAM')"
    # query_string = "SELECT CreatedDate,ContentDocumentId,ContentLocation,FileExtension,FileType,Id,Title,VersionData FROM ContentVersion where FileExtension='pdf'"
    query_string = "SELECT CreatedDate,ContentDocumentId,ContentLocation,FileExtension,FileType,Id,Title,VersionData FROM ContentVersion where FileExtension='pdf' and ContentDocumentId IN "+finalcondocsids
    print('Query'+query_string)
    sfcondocsnew = sf.query(query_string)
    output_directory =ParentRecordId
    fetch_files(sf,query_string,output_directory)
    
    # Creating a pdf file object.
    print("\x1b[1;32m" + "Reading the PDF File" + "\x1b[0m") 
    basepath = output_directory
    insertjsondata = {};
    insertdata = [];
    for entry in os.listdir(basepath):
        try:
            if os.path.isfile(os.path.join(basepath, entry)):
                print('&&&&'+basepath)
                print('%%%%'+entry)
                name, ext = os.path.splitext(entry)
                if ext =='.pdf':
                    print('###'+entry)
                    pdf = open(basepath+"/"+entry, "rb")
                    # Creating pdf reader object.
                    pdf_reader = PyPDF2.PdfFileReader(pdf)
                    # Checking total number of pages in a pdf file.
                    print("Total number of Pages:", pdf_reader.numPages)
                    pgno = pdf_reader.numPages
                    # Creating a page object.
                    for x in range(pgno):
                        print('Page '+str(x)+' Content')
                        page = pdf_reader.getPage(x)
                        # Extract data from a specific page number.
                        # if x==0:
                        text = page.extractText().encode('utf-8')
                        search_text = " ".join(text.replace("\xa0", " ").strip().split())     
                        search_line = search_text.split(".")
                        # Iterate each Key Word
                        for search_term in searchkewwords:
                            # print(search_term)
                            # Search on each line
                            for word in search_line:
                                if search_term in word.decode("utf-8"):
                                    # print (search_term)
                                    # print (word) 
                                    insertjsondata['Question__c']= search_term
                                    insertjsondata['Answer__c']= word
                                    json_data = json.dumps(insertjsondata)
                                    insertdata.append(json_data)  

                    # Closing the object.
                    pdf.close()
                    # print(insertdata)
        except:
            print("An exception occurred while reading the PDF")
    
    # print(insertdata)
    insertdatalen = len(insertdata)
    print (insertdatalen)
    # data = [
    #   {"LastName":"\'%#!/)\'0\'!11con1","Email":"example@example.com"},
    #   {"LastName":"\'%#!/)\'0\'!112$&!#$*3 \Con2","Email":"test@test.com"}
    # ]
    # sf.bulk.contact.insert(data)

    formatinsertdata=(",".join(insertdata))
    finalsinsertdata = "["+formatinsertdata+"]"
    print(finalsinsertdata)
    if insertdatalen > 0:
        sf.bulk.Question_Answer__c.insert(json.loads(finalsinsertdata))
    # data = [{"Question__c": "Outcomes", "Answer__c": "'%#!/)'0'!112$&!#$*3 'OUTCOMES Key Outcomes Progress Indicators In order to monitor progress, we will be gathering information by keeping records of attendance and participation to all ADF pro jects and events"}]
    # sf.bulk.Question_Answer__c.insert(data)
    # deletefilesandfolder(output_directory)
    

    # # Remove the Files & Folder
    # filelist = [ f for f in os.listdir(output_directory)]
    # for f in filelist:
    #     # print(f)
    #     os.remove(os.path.join(output_directory, f))
    # os.rmdir(output_directory)
    # print('####Removed the directory and files')






    
def deletefilesandfolder(output_directory):
    filelist = [ f for f in os.listdir(output_directory)]
    for f in filelist:
        # print(f)
        os.remove(os.path.join(output_directory, f))
    os.rmdir(output_directory)
    print('####Removed the directory and files')


def fetch_files(sf,query_string, output_directory):
    attachment = sf.query(query_string)
    files = 0
    already_downloaded = 0
    existing_filenames = {}
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)
    while attachment:
        print('****')
        for r in attachment["records"]:
            content_document_id = r["ContentDocumentId"]
            # title = r["Title"]+"."+r["FileExtension"]
            # title = ''.join(e for e in r["Title"] if e.isalnum())+"."+r["FileExtension"]
            title = ''.join(e for e in r["Title"] if e.isalnum())+".pdf"
            filename = "%s/%s" % (output_directory, title)
            url = "https://%s%s" % (sf.sf_instance, r["VersionData"])
            created_date = r["CreatedDate"]
            
            
            if not os.path.isfile(filename):
                response = requests.get(url, headers={"Authorization": "OAuth " + sf.session_id,
                                                      "Content-Type": "application/octet-stream"})
                if response.ok:
                    print ("Saving %s" % title)
                    with open(filename, "wb") as output_file:
                        output_file.write(response.content)
                    existing_filenames[title] = created_date
                    files += 1
                else:
                    print ("Couldn't download %s" % title)
            else:
                if title not in existing_filenames:
                    existing_filenames[title] = created_date
                else:
                    print ("%s (%s) already in list (%s)" % (title, existing_filenames[title], created_date))
                already_downloaded += 1
        if "nextRecordsUrl" in attachment:
            next_records_identifier = attachment["nextRecordsUrl"]
            query_response = sf.query_more(next_records_identifier=next_records_identifier, identifier_is_url=True)
        else:
            print ("%d files downloaded" % files)
            print ("%d already downloaded" % already_downloaded)
            break


if __name__ == "__main__":
    main()  
