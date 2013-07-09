from plone.namedfile.file import NamedBlobFile
import os
import random

def get_random_file(path):
    abs_path = os.path.abspath(path)
    files = []
    for item in os.listdir(abs_path):
        if os.path.isfile(abs_path + '/' + item):
            files.append(abs_path  + '/' + item)
    if len(files) == 0:
        raise KeyError("No files were Found in the given folder")
    filename = random.choice(files)
    file_ = open(filename, 'r')
    blob_file = NamedBlobFile(data=file_.read(), filename=os.path.basename(file_.name.decode('utf-8')))
    file_.close()
    return blob_file
