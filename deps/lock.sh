#/bin/bash
#
# Lock our dependencies from the .in files using uv

for file in deps/*.in; do 
  file_noext="${file%.*}"
  uv pip compile "$file" -o "$file_noext.txt" 
done 
