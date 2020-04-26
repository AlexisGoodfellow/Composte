FROM centos:latest

USER root

# Grab dependencies
RUN yum -y groupinstall "Development Tools"
RUN yum -y install openssl-devel bzip2-devel libffi-devel qt5-qtbase-devel sqlite-devel
RUN curl -s https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tgz | tar -xvzf -

# Build Python from source and symlink 3 -> 2
WORKDIR Python-3.8.2

RUN ./configure --enable-loadable-sqlite-extensions --enable-optimizations && make install
RUN ln -fs /usr/local/bin/python3 /usr/local/bin/python
RUN ln -fs /usr/local/bin/pip3 /usr/local/bin/pip
RUN pip install --upgrade pip setuptools

# Go back to app context
WORKDIR /app

COPY . .

RUN pip install -r requirements-test.txt -r requirements.txt

EXPOSE 5000 5001

CMD ["/bin/bash"]
# CMD [ "python", "./ComposteServer.py" ]
