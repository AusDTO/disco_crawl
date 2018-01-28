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

ADD ./scripts /src/scripts
ADD ./settings.py /src/
ADD ./base_node.py /src/
ADD ./es2kinesis.py /src/
ADD ./process_bs4.py /src/
ADD ./process_goose.py /src/
ADD ./process_raw.py /src/
#ADD ./process_textract.py /src/
ADD ./simple_node.py /src/

# stuff textract needs
#RUN apt-get install -y swig gcc libpulse-dev libjpeg-dev \
#    build-essential git make \
#    python-dev libxml2-dev libxslt1-dev antiword unrtf \
#    tesseract-ocr libjpeg-dev poppler-utils pstotext \
#    flac ffmpeg lame libmad0 libsox-fmt-mp3 sox
#
#RUN apt-get install -y zlib1g-dev
#RUN apt-get install -y libpocketsphinx-dev libpocketsphinx3
#
#RUN pip install -U EbookLib==0.16
#RUN pip install -U pocketsphinx
#RUN pip install textract
