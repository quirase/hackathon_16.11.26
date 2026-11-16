from transcript_parser import get_transcript

# Your YouTube link
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Get transcript
result = get_transcript(url)

# Print the dictionary
#print(result)

#суцільний текст
print(result[1])

#словник зі структурою 'word':[], 'time_code':[]
print(result[0])