# RAW SOCKET PROGRAMMING
Computer Networking - Project 4 
Project by - Mariah Maynard and Shriya Dhaundiyal

## **UNDERSTANDING PROJECT DESGIN**

In order to start this project, we needed an in-depth understanding of the OSI model and the role of each layer. 
This project required us to get familiar with low-level operations of the internet protocol stack. We had to go beyond implemeting application level protocols (HTTP GET/ RECEIVE) and build IP and TCP headers in each packet for sending and receicing data.

We based our understanding of the project on the following steps:

![image](https://user-images.githubusercontent.com/110204529/223234905-8aa8832b-09da-48c8-aa6f-6955c91509cd.png)

As the data flows down the different layers, each layer attaches a header to it. When a client program wants to connect to a server, it creates a GET request and passes it down to the TCP layer. The TCP layer creates a TCP packet with the TCP header and the GET request and passes it down to the IP layer. The IP layer further attaches its own header to the TCP segment and creates a IP Datagram ( IP HEADER + TCP HEADER + DATA ) and sends it down to the data link/ ethernet layer.

![image](https://user-images.githubusercontent.com/110204529/223235111-f7cedea4-3d6e-4dd2-b8ef-9a25460fcfe0.png)

Our program design for sending data is also based on the same network flow: 

**APPLICATION LAYER ----> DATA**<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        V<br>
**TCP LAYER ----> TCP SEGMENT ( DATA + TCP HEADER)**<br>
 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        |<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;        V<br>
**IP LAYER ----> IP DATAGRAM ( DATA + TCP HEADER + IP HEADER)**<br>





