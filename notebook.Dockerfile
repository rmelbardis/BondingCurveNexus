FROM jupyter/datascience-notebook
ADD requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt
