# Shahnama

This repository contains the Shahnama software developed at Caret, University of Cambridge and licensed open source under the AGPL license. 

Before using please read the LICENSE file contained in this repository.

Before contributing please read the LICENSE and NOTICE file contained within this repository.

We have chosen to make this software open source to allow others to use it and we have chosen the AGPL license to encourage others to contribute modifications and extensions back to the wider community in some form. Obviously we would not expect or ask anyone to contribute modifications and extensions containing to private or security related information back to the wider community.


# Introduction

The software is a standard DJango application for installation and deployment consult the documentation at the DJango website.

The application itself consists of 2 parts. A simple Content model that manages authored pages, and a metadata model for providing views onto the metadata associated with the manuscripts. The application allows view, creation, editing and deletion of the content model. The application only allows view of the metadata model, with data being ingested into the application via an administrator managed load process.

## Dependencies

The application requires python image utilities, which can be installed with `$ easy_install pil`

## Data loading.

Data loading is a 2 step process. There is a script, Migrate.py that creates json files, one per record from the existing meta data database (currently a MySQL instance). This is run on the commandline and requires access to that database. The json files are loaded via a administrative web UI into the Django model which is stored in whichever RDBMS backend the Django instance is configured to use. 

The content model is populated by loading JSON files from disk using the same web UI. Once loaded the content pages can be edited by a suitably authenticated user in the web UI.

# Deployment

Any standard deployment method for Django can be used. If deploying for production you may want to use an alternative authentication framework (eg SSO), and you should look at configuring caching. The responses at each URL are cacheable and vary by URL. Doing this will eliminate all database load from the system.

You should consult the 


# Credits

* The work was funded by : ?
* Original code largely written by Dan Shepard whilst at Caret
* For other contributions, please consult the commit history.

(c) 2011 University of Cambridge


