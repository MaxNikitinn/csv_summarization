# .csv Summarizer
This project provides descriptive statitics on each column of the dataframe.

Input: .csv file
Output: markdown, html or excel file.

Descriptive statistics:

Numerical values:
- min value
- max value
- mean value
- median value
- proportion of zero rows
- variance
- std
- interquartile range
- result of ks normality test
- number of unique values (for integer type only)
- orderliness (for integer type only)
- density (for integer type only)

Nominal values:
- number of unique values
- most common value
- number of occurances of the most common value

Datetime values:
- start of the datatime range
- end of the datetime range
- timespan of the column
- orderliness
