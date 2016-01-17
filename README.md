rdb-fullstack
=============

Modified code for the Relational Databases and Full Stack Fundamentals courses

Tournament Code
===============

Tournament code creates a database with players and thier matches. tournament.py contains helper functions to perform various actions on the databse such as: adding players, reporting matches, deleting players, and matching players based on skill. Tournament_test performs code tests to verify that all functions in tournament.py are working as inteded.

TO RUN:
1. Make sure you have Virtual Box and Vagrant installed. (https://www.virtualbox.org/, https://www.vagrantup.com/)
2. Clone the repo to your machine 
3. Navigate to the vagrant folder inside of the cloned repo at /fullstack-nanodegree-vm/vagrant
4. Run Vagrant Up to boot VM ad install necessary requirements (this will run for a minute or two).
5. In the same directory run "vagrant ssh" to ssh into the VM
6. Once inside the VM navigate to the tournament code directory "cd /vagrant/tournament"
7. First we will need to create the database and schemas. To do this type 'psql' in the command prompt
8. Inside of the psql prompt run tournament.sql as a psql query. "\i tournament.sql". This will create the database and necessary tables.
9. Exit the psql prompt by typing "\q"
10. We are now ready to run the tournament_test python file. 
11. To run the python test file simply type "python tournament.py" (given you are still in the /vagrant/tournament directory)
12. If done properly test should display "Success!  All tests pass!"



