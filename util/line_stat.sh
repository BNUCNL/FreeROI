# line number of .py file
find .. -name "*.py" | xargs wc -l

# line number of .py & .md files
# find .. -name "*.py" -or "*.md" | xargs grep -v "^$" | wc -l
