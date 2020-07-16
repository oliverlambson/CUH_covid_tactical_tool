FROM continuumio/anaconda3

# Grab requirements.txt.
# conda env export --no-builds
# conda env export --from-history
ADD ./environment.yml /tmp/environment.yml

# Add our code
ADD . /opt/webapp/
WORKDIR /opt/webapp

RUN conda env create --file /tmp/environment.yml -n env
RUN echo "source activate env" > ~/.bashrc
ENV PATH /opt/conda/envs/env/bin:$PATH
# SHELL ["conda", "run", "-n", "app", "/bin/bash", "-c"]

# CMD voila --port:$PORT --no-browser --enable_nbextensions=True --TagRemovePreprocessor.remove_cell_tags='{"hide"}' --VoilaConfiguration.file_whitelist="['(app.ipynb)|(robots.txt)']" app.ipynb
CMD voila \
 --port=$PORT \
 --no-browser \
 --enable_nbextensions=True \
 --TagRemovePreprocessor.remove_cell_tags='{"hide"}' \
 --VoilaConfiguration.file_whitelist="['(app.ipynb)|(robots.txt)']" \
 app.ipynb

# voila --port=$PORT --no-browser --enable_nbextensions=True --TagRemovePreprocessor.remove_cell_tags='{"hide"}' --VoilaConfiguration.file_whitelist="['(app.ipynb)|(robots.txt)']" app.ipynb
# voila --port=3000 --no-browser --enable_nbextensions=True --TagRemovePreprocessor.remove_cell_tags='{"hide"}' --VoilaConfiguration.file_whitelist="['(app.ipynb)|(robots.txt)']" app.ipynb