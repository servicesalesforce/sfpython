import PyPDF2
import json
import os
import os.path
from PyPDF2 import PdfFileReader
from simple_salesforce import Salesforce, SFType, SalesforceLogin
import requests



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
    
    # query_string = "SELECT CreatedDate,ContentDocumentId,ContentLocation,FileExtension,FileType,Id,Title,VersionData FROM ContentVersion where ContentDocumentId='069B0000006rXmQIAU'"
    query_string = "SELECT CreatedDate,ContentDocumentId,ContentLocation,FileExtension,FileType,Id,Title,VersionData FROM ContentVersion where FileExtension='pdf'"
    output_directory ="069B0000006rXmQIAU"
    fetch_files(sf,query_string,output_directory)
    
    # Creating a pdf file object.
    print("\x1b[1;32m" + "Reading the PDF File" + "\x1b[0m")
    pdf = open("BAC.pdf", "rb")
    # Creating pdf reader object.
    pdf_reader = PyPDF2.PdfFileReader(pdf)
    # Checking total number of pages in a pdf file.
    print("Total number of Pages:", pdf_reader.numPages)
    pgno = pdf_reader.numPages
    # Creating a page object.
    for x in range(pgno):
        print('Page '+str(x)+' Content')
        page = pdf_reader.getPage(x-1)
        # Extract data from a specific page number.
        print(page.extractText())

    # Closing the object.
    pdf.close()




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
            title = r["Title"]
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
