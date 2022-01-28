FROM golang:1.16.10-alpine3.14 as build
RUN apk add --no-cache git make py-pip
RUN pip install hstk
WORKDIR /go/src/github.com/ibm/sofa-storage/csi-plugin/
ADD . ./
RUN make sofa-storage-csi

FROM alpine:3.14
# Install required packages
RUN apk add --no-cache nfs-utils qemu-img ca-certificates xfsprogs e2fsprogs e2fsprogs-extra xfsprogs-extra zfs btrfs-progs py-pip
RUN pip install hstk
WORKDIR /sofa-csi-plugin/
# Copy plugin binary from first stage
COPY --from=build /go/src/github.com/ibm/sofa-storage/csi-plugin/build/sofa-storage-csi .
COPY run_sofa_csi.sh .
#ENTRYPOINT ["/sofa-csi-plugin/sofa-storage-csi"]
ENTRYPOINT ["sh", "/sofa-csi-plugin/run_sofa_csi.sh"]