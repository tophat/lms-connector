FROM python:3.7.2

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

ENV AM_I_IN_A_DOCKER_CONTAINER yes

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

RUN curl -O https://nodejs.org/download/release/v8.6.0/node-v8.6.0-linux-x64.tar.gz
RUN tar -C /usr/local --strip-components 1 -xzf node-v8.6.0-linux-x64.tar.gz
RUN rm node-v8.6.0-linux-x64.tar.gz

RUN apt-get update || (apt-get install -y apt-transport-https && apt-get update)
RUN apt-get install -y yarn

RUN pip3 install pipenv
