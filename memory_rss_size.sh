#!/bin/ksh
# Effectue la somme des SIZE et RSS de tous les process
# Si on fourni un argument on fait un grep dessus.
if [ $# = 0 ]
then
   echo " Liste complete de tous les processus/threads avec gvww :"
   echo "#########################################################"
   ps gvww | sort -n -k 6,6 
   echo
   echo
   echo " Liste complete de tous les processus/threads avec guww :"
   echo "#########################################################"
   ps guww | sort -n -k 4,4 
else
  if [ $# = 1 ]
  then 
    echo " On ne liste que les lignes contenant [$1] :"
    ps gvww | sort -n -k 6,6 | grep $1 | grep -v mem.ksh | grep -v grep
  else
    echo "  Erreur sur le nombre d'arguments."
    exit 1
  fi
fi
　
echo
ps gvww | grep -e SIZE -e RSS | grep -v grep
echo
echo
echo "PGIN: (v flag) The number of disk I/Os resulting from references by the process to pages not loaded in core."
echo "SIZE:  (v flag) The virtual size of the data section of the process (in 1KB units)."
echo "RSS:   (v flag) The real-memory (resident set) size of the process (in 1KB units)."
echo "SSIZ:  (s flag) The size of the kernel stack. This value is always 0 (zero) for a multi-threaded process."
echo "SZ:    (-l and l flags) The size in 1KB units of the core image of the process."
echo "LIM: (v flag) The soft limit on memory used, specified via a call to the setrlimit"
echo "      subroutine. If no limit has been specified, then shown as xx. If the limit is"
echo "      set to the system limit, (unlimited), a value of UNLIM is displayed."
echo "TSIZ:  (v flag) The size of text (shared-program) image."
echo "TRS:   (v flag) The size of resident-set (real memory) of text."
echo "%MEM:  (u and v flags) The percentage of real memory used by this process."
echo
echo
echo "Total-SIZE  Total-RSS  Total-TSIZ  Total-TRS  Total-%MEM"
ps gvww | grep -v PID | awk '{cpt6=cpt6+$6; cpt7=cpt7+$7; cpt9=cpt9+$9; cpt10=cpt10+$10; cpt12=cpt12+$12} END{print cpt6, "   ", cpt7, "   ", cpt9, "   ", cpt10, "   ", cpt12, "   ", cpt12 * 1024 * 1024 * 1024 * 8 / 100}' 
　
　
