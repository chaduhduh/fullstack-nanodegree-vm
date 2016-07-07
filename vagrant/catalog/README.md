Catalog Code
===============


This catalog utilizes the Flask framework to provide the basis for any list type web application. The demonstration 
provided is setup as blog in which users can add posts and tag them with the appropriate category. This could really 
be used for any list type of application, such as: tutorials, products, reviews etc.<br /><br />
![Alt text](application/static/images/preview.jpg?raw=true "Preview")<br />
<br />

<b>To Run:</b><br />
1. Go through environment setup steps if necessary<br />
3. Navigate to the vagrant folder inside of the cloned repo at /fullstack-nanodegree-vm/vagrant<br />
4. Run "Vagrant Up" to boot VM and run "vagrant ssh" to connect to the VM<br />
6. Once inside the VM navigate to the catalog code directory "cd /vagrant/catalog"<br />
7. Navigate to the application directory "cd application"<br />
8. We can start our flask application by running the file named application.py - "python application.py"<br />
9. We can now view this application at http://localhost:5000

Api Routes
===============

A quick list of available JSON endpoints are listed below. These can be used to extend this 
to any platform that can make http requests.

http://localhost:5000/Item/ - GET /{ model }/  <br />
http://localhost:5000/Item/1 - GET /{ model }/{ id }  <br />
http://localhost:5000/Category/ - GET /{ model }/  <br />
http://localhost:5000/Category/Item/ - GET /{ model }/{ model } <br />

