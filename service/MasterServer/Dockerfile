# For 1. latest stable python
#     2. relative fast build speed
#     3. small image size
#     4. application performance and security
# We choose the amazon linux
# Refer to `https://zhuanlan.zhihu.com/p/578256741`  
# for more about size and build speed.
FROM amazonlinux:latest

RUN yum update -y && yum install python3 python3-pip -y
    
# Copy the directory to image's destination. 
COPY . /MasterServer

# Set the working directory
WORKDIR /MasterServer

# Install the chatbot dependencies
RUN pip3 install -r /MasterServer/requirements.txt

# Select an entry point
ENTRYPOINT [ "python3" ]

# Running the program
CMD [ "src/app.py" ]