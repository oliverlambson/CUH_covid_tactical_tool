FROM continuumio/miniconda3

# Grab requirements.txt.
ADD ./environment.yml /tmp/environment.yml

# Add our code
ADD . /opt/webapp/
WORKDIR /opt/webapp

RUN conda env create --file /tmp/environment.yml -n env \
 && echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH

RUN useradd -m myuser
USER myuser
CMD voila \
 --port=$PORT \
 --no-browser \
 --enable_nbextensions=True \
 --TagRemovePreprocessor.remove_cell_tags='{"hide"}' \
 --VoilaConfiguration.file_whitelist="['(app.ipynb)|(robots.txt)']" \
 app.ipynb
