
var1=""

until [ "$var1" == "exit" ]
do
    echo "Please enter one of the following:"
    echo "-----------------------------------"
    echo "\"svm\"  | to run SVM experiments"
    echo "\"grid\" | to run SVM GridSearch."
    echo "\"exit\" | to exit."

    read var1

    if [ "$var1" == "grid" ]
    then
        echo "WARNING: GridSearch will take days to complete"
        echo "please confirm y/n"
        read confirm
        if [ "$confirm" == "y" ]
        then
            python gridSearchMain.py
        else
            echo "GridSeach aborted"
        fi
    fi

    if [ "$var1" == "svm" ]
    then
        echo "running SVM experiments"
        python svmMain.py
    fi

    echo " "
    echo " "
done
