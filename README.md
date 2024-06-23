This repo contains files and scripts for our Master's thesis:
[Exploring JPEG File Containers Without Metadata: A Machine Learning Approach for Encoder Classification](https://urn.kb.se/resolve?urn=urn:nbn:se:hh:diva-53596)

Below is the steps we used to construct the TSV used for ML processing.

The process is a bit hacky and ugly and could probably be done in much cleaner way, but we basically performed the below steps to construct the tsv. These are for the Forchheim image data set, but the process was very similar for the Floreview one. The final tsv used (`floraview_forchheim.tsv`) is concatenation of these two extractions.

1) `jpmarkers2.py` is custom script that always removes image data from a jpeg (the ECS "segment"), along with the marker segments specified with `-r`. This is because we are not interested in the image data and to have smaller files to work with in the next steps.
```bash
for f in *.jpg; do
    jpmarkers2.py -r APP1,APP2,APP3,APP4,APP5,APP6,APP7,APP8,APP9,APP10, \
                     APP11,APP12,APP13,APP14,APP15,RST0,RST1,RST2,RST3,RST4, \
                     RST5,RST6,RST7 \
                  -i $f -o cleaned_$f
done
```

2) Extract features with `fq` and pipe through `jq` for pretty printing.

```bash
for f in cleaned_*.jpg; do
    fq -r '.|tojson' $f | jq . > $(basename -s .jpg $f).json;
done
```

3) Transform the json output from `fq` to tsv and also do some slight post-processing like concatinating qtables to hexstrings among other small things.
```bash
for f in *.json; do
    transform.py < $f > tsv/$(basename -s .jpg $f).tsv;
done
```

4) Extract headers from all TSV files and combine them into a single list of unique headers
```bash
for file in *.tsv; do
    head -1 "$file" >> all_headers.tsv
done
sort -u all_headers.tsv > unique_headers.tsv
```

5) concatenate TSVs and align columns:
```bash
05_tsv_fix.py tsv/ combined.tsv
```

6) Join on IDs to get columns for manufacturers, date etc.
```bash
add_ids_and_more.py combined.tsv IDs.tsv combined_with_IDs.tsv
```
