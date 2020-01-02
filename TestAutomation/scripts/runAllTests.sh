#! bash

# AJ Williams, Shaina Mainar, David  via Seawolves
# call explicitly from TestAutomation Folder with "bash ./scripts/runAllTests.sh" from testCasesExcecutables
# if it doesn't run
# do "chmod 755 ./scripts/runAllTests.sh" (without the quotation marks)
# try again

# runs every test in the testCase folder and outputs an html document with results available in reports folder

# **********
#might need to know output type
#fix array problems

# goto testCases
#cd ..
cd testCases

# array where the files of the testCases are kept
testCaseArray=($(ls))

#echo ${testCaseArray[*]}
#echo ${testCaseArray[4]}
# array where results of tests are stored
results=()
failures=()

# get the date
currentDate=$(date)

i=0
length=${#testCaseArray[@]}

# loops through test cases with i
for ((i=0;i<length;i++))
do
	input=${testCaseArray[$i]}
	# input=testCase0.txt if you only want to do a specific case

	j=0
	# reading lines of testCase
	while IFS= read -r line
	do
		if [ $j -eq 0 ]
			then testCase=$line
		fi
		if [ $j -eq 1 ]
			then requirement=$line
		fi
		if [ $j -eq 2 ]
			then driver=$line
		fi
		if [ $j -eq 3 ]
			then driverMethod=$line
		fi
		if [ $j -eq 4 ]
			then testInput=$line
		fi
		if [ $j -eq 5 ]
			then oracle=$line
		fi
		j=$((j+1))
	done < "$input"
	
	# goto python file folder
	cd ..
	cd project
	cd src

	# run driver or python file directly
	driverOutput=$(python -c "import $driver; print($driverMethod($testInput))")
	# echo $driverOutput

	# compare numbers
	if [ $driverOutput = $oracle ]
		then result=("Pass")
	else 
		result=("FAIL!")
		#failures+=("<tr><td>$testCase</td><td>$requirement</td><td style=\"word-wrap: break-word\">$driverMethod</td><td>$testInput</td><td style=\"word-wrap: break-word\">$driverOutput</td><td style=\"word-wrap: break-word\">$oracle</td><td>$result</td></td>")
	fi
	# compare strings use = instead
	# result="whatever"
	# store results-- also using html tags here for table layout
	results+=("<tr><td>$testCase</td><td>$requirement</td><td style=\"word-wrap: break-word\">$driverMethod</td><td>$testInput</td><td style=\"word-wrap: break-word\">$driverOutput</td><td style=\"word-wrap: break-word\">$oracle</td><td>$result</td></td>")

	#goto cases folder
	cd ..
	cd ..
	cd testCases
done

# goto results folder
cd ..
cd reports


# produce html document with style
FILENAME=testResults.html
cat <<- _Output > $FILENAME
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
#results {
  font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
}

#results td, #results th {
  border: 1px solid #ddd;
  padding: 8px;
}

#results tr:nth-child(even){background-color: #f2f2f2;}

#results tr:hover {background-color: #ddd;}

#results th {
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: left;
  background-color: #4CAF50;
  color: white;
}
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
}

.top-container {
  background-color: #f1f1f1;
  padding: 30px;
  text-align: center;
}

.header {
  <!--padding: 10px 16px;-->
  background: #555;
  color: #f1f1f1;
}

.content {
  <!--padding: 16px;-->
}

.sticky {
  position: fixed;
  top: 0;
  width: 100%;
}

.sticky + .content {
  padding-top: 102px;
}
</style>
</head>
<body>
<div class="top-container">
Sugar Desktop App<br>
$currentDate
  <h1>Test Results</h1>
</div>

<div class="header" id="myHeader">
<table id="results">
<col width="100">
  <col width="125">
  <col width="300">
  <col width="200">
  <col width="200">
  <col width="200">
  <col width="75">
  <tr>
    <th>Test Case</th>
    <th>Requirement</th>
    <th>Method</th>
    <th>Input</th>
    <th>Output</th>
    <th>Oracle</th>
    <th>Result</th>
  </tr>
  </table>
</div>

<div class="content">
  <table id="results">
  <col width="100">
  <col width="125">
  <col width="300">
  <col width="200">
  <col width="200">
  <col width="200">
  <col width="75">


		${results[*]}
		
</div>

<script>
window.onscroll = function() {myFunction()};

var header = document.getElementById("myHeader");
var sticky = header.offsetTop;

function myFunction() {
  if (window.pageYOffset > sticky) {
    header.classList.add("sticky");
  } else {
    header.classList.remove("sticky");
  }
}
</script>

</body>
</html>

_Output

xdg-open $FILENAME

