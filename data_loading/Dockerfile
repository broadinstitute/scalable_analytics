# Start from this container so that numpy and all its dependencies are present.
FROM gcr.io/cloud-datalab/datalab

# Add the Python HDF5 package.
RUN pip install tables

COPY hdf5_to_sparse.py /opt/

ENTRYPOINT ["bash"]
