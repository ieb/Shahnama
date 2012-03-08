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

Please note all commands are run in `src/ShahnamaDJ/` where manage.py is located.


## Step 1: Edit settings.py

First edit settings.py. You will need to adjust any absolute paths in there, and may wany to select a different database type than sqllite if you are running in production. Note that SOURCE_DATA is relevent to the migration process and contains example editorial content.

## Step 2: Migrate data from a Shahnama Database.

Data is migrated using the `Migrate.py` script. That script contains a MySQL connection which will need to be edited to point to the existing shahnama database. Running this script will extract all the data and create thousands of files under the location specified by `SOURCE_DATA` in `settings.py`

## Step 3: Create the database schema

If you are not using sqllite, you will have to create a user in the database as per your `settings.py`, and allow that user to create tables, indexes etc. Django recommends PostgreSQL.

Once you have done that, run `python manage.py syncdb` to create the database. You will be asked for an admin user, please make certain that you use a secure password if you are going to make the `/admin` URL visible to the world.

## Step 4: Start the development server

Start the development server, so that you can load the data. Please DO NOT use the development server to run in production, go and read the Django documentation (and use mod_python as recommended)/\.

Run `python manage.py runserver`

## Step 5: Login as the admin user.

Login as the admin user (created in Step 3) and go to `http://localhost:8080/admin/loadDb`. At this page, read the instructions and load the database with the Shahnama data you migrated in step 2. Remember to tick the checkbox so that it loads the data. If you don't the loadDB action will only check and resolver internal references. 

## Step 6: Load Editorial Content (Optional)

You can also load editorial content from SOURCE_DATA/content on `http://localhost:8080/admin/loadDb`. Once you have loaded this content (there are example files in the source repository), you can edit them online. Any user in the DJango database with content.pageedit, content.createpage, content.pageview, content.imageupload can perform those actions on editorial content. Consult the Django documentation on how to give users permissions. content.pageview allows users to see a list of all content pages.


# Deployment

Any standard deployment method for Django can be used. If deploying for production you may want to use an alternative authentication framework (eg SSO), and you should look at configuring caching. The responses at each URL are cacheable and vary by URL. Doing this will eliminate all database load from the system.

You should consult the Django documentation for information on deployment and configuration with SSO systems.


# Testing

The code base uses DJango unit tests. Some of the test use fixtures. The following fixtures are used during testing. `src/ShahnamaDJ/contenttest.json` and `src/ShahnamaDJ/recordstest.json`. Thes can be created by dumping your working DJango database `python manage.py dumpdata`. If you choose to run Django unit tests ie `python manage.py test` with a complete database in recordstest.json (ie abotu 44MB of json) the test suite will load and validate all 30K+ pages which will take about 1H. (Unit tests are single threadded)


# Credits

* The work was funded by : ?
* Original code largely written by Dan Shepard whilst at Caret
* For other contributions, please consult the commit history.

(c) 2011 University of Cambridge


