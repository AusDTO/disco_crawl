FROM ubuntu:17.10

RUN apt-get update \
&& apt-get install -y software-properties-common curl \
&& apt autoremove -y \
&& apt-get update \
&& apt-get remove -y software-properties-common \
&& apt-get install -y python3.6 \
&& curl -o /tmp/get-pip.py "https://bootstrap.pypa.io/get-pip.py" \
&& python3.6 /tmp/get-pip.py

ENV PYTHONUNBUFFERED 1

ADD ./requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install -r requirements.txt

RUN pip install pyphen
RUN mkdir tmp &&  cd tmp \
    && apt-get install -y git \
    && apt-get autoremove -y \
    && git clone https://github.com/wimmuskee/readability-score.git \
    && cd readability-score \
    && python3.6 setup.py build \
    && python3.6 setup.py install \
    && cd ../.. \
    %% rm -rf tmp

ADD ./scripts /src/scripts
RUN python3.6 scripts/setup_nltk.py

ADD ./settings.py /src/
ADD ./base_node.py /src/
ADD ./es2kinesis.py /src/
ADD ./process_bs4.py /src/
ADD ./process_goose.py /src/
ADD ./process_raw.py /src/
ADD ./process_readability.py /src/
# ADD ./simple_node.py /src/
