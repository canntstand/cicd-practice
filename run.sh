#!/bin/bash

for n in {1..5}
do 
    touch "file${n}.txt"
    echo ${n} > "file${n}.txt"
done