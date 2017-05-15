#!/bin/sh
　
# prend en entrÃ©e le nom du code a retrouver dans l'accounting SGE puis le nom de l'utilisateur pour lequel on veut compte le nombre d'usage du code.
　
code=$1
utilisateur=$2
　
if [ $# = 0 ] 
then
  echo "Erreur, il manque le paramÃ¨tre code_de_calcul et/ou utilisateur."
  exit 1
fi
　
if [ ! $# = 1 -a ! $# = 2 ]
then
  echo "Erreur, sur le nomber de paramÃ¨tres."
  exit 1
fi
　
if [ $# = 1 ]
then
  echo "On considÃ¨re que le paramÃ¨tre est le nom du code de calcul."
fi
　
echo "Usage du code $1:"
echo "#######################"
qacct -j | grep -e owner -e account -e jobname -e jobnumber -e start_time -e slots | awk -v code=$code '{ ligne1=$0;getline;ligne2=$0;getline;ligne3=$0;getline;ligne4=$0;getline;ligne5=$0; getline; ligne6=$0; if (match(ligne4,code)) {print ligne1, ligne2, ligne3, ligne6;print ligne4, ligne5; print ""}}'
　
echo
if [ $# = 2 ]
then
  echo "Usage du code $1 par l'utilisateur $2:"
  echo "###########################################"
  qacct -j | grep -e owner -e account -e jobname -e jobnumber -e start_time -e slots | awk -v code=$code '{ ligne1=$0;getline;ligne2=$0;getline;ligne3=$0;getline;ligne4=$0;getline;ligne5=$0; getline; ligne6=$0; if (match(ligne4,code)) {print ligne1, ligne2, ligne3, ligne6;print ligne4, ligne5; print ""}}'  | grep $utilisateur 
fi
　
echo
if [ ! $# = 2 ]
then
  echo "Nombre et liste d'utilisateur du code:"
  echo "######################################"
  qacct -j | grep -e owner -e account -e jobname -e jobnumber -e start_time -e slots | awk -v code=$code '{ ligne1=$0;getline;ligne2=$0;getline;ligne3=$0;getline;ligne4=$0;getline;ligne5=$0; getline; ligne6=$0; if (match(ligne4,code)) {print ligne1, ligne2, ligne3, ligne6;print ligne4, ligne5; print ""}}'  | grep "owner" | awk '{ print $1, $2}'| sort -u
  echo
  echo "Nombre d'executions du code $1 pour tous les utilisateurs:"
  echo "##########################################################"
  qacct -j | grep -e owner -e account -e jobname -e jobnumber -e start_time -e slots | awk -v code=$code '{ ligne1=$0;getline;ligne2=$0;getline;ligne3=$0;getline;ligne4=$0;getline;ligne5=$0; getline; ligne6=$0; if (match(ligne4,code)) {print ligne1, ligne2, ligne3, ligne6;print ligne4, ligne5; print ""}}'  | grep "owner" | wc
else
  echo "Nombre d'executions du code $1 par l'utilisateur $2:"
  echo "###########################################"
  qacct -j | grep -e owner -e account -e jobname -e jobnumber -e start_time -e slots | awk -v code=$code '{ ligne1=$0;getline;ligne2=$0;getline;ligne3=$0;getline;ligne4=$0;getline;ligne5=$0; getline; ligne6=$0; if (match(ligne4,code)) {print ligne1, ligne2, ligne3, ligne6;print ligne4, ligne5; print ""}}'  | grep $utilisateur | wc
fi
　
　
　
