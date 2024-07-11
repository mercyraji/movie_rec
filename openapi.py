import os
import openai
from openai import OpenAI

# Set environment variables
my_api_key = 'OPENAI_API_KEY'

openai.api_key = my_api_key

# Create an OpenAPI client using the key from our environment variable
client = OpenAI(
    api_key=my_api_key,
)


def ask_ai(prompt):
    # Specify the model to use and the messages to send
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt}
        ]
    )
    return (completion.choices[0].message.content)


def get_movie_recommendation(films, ratings, genre, age_rating, year_range):
    prompt = (
        f"Using this list of films watched by a user: {films} and the ratings out of 5 they gave these films: {ratings}, "
        f"can you give a movie recommendation? The user prefers {genre} genre, with an age rating of {age_rating}, "
        f"and movies released in the years {year_range} inclusive."
        f"Please only output a numbered list of 5 movies and a sentence-long plot summary for each.")
    return ask_ai(prompt)


def get_trivia(films):
    prompt = (
        f"From this list of films watched by a user: {films}, take one film and generate 5 movie trivia questions based on that film with the answer posed as a muliple choice questions include only 3 answers to choose from")

    return ask_ai(prompt)


def parse_trivia_response(response):
    """
    Parses the trivia response to extract a list of questions, posed answers, and correct answers.
    """
    # Split the response into lines
    lines = response.strip().split('\n')

    trivia_data = []
    question = None
    posed_answers = []
    correct_answer = None  # Initialize correct_answer

    for line in lines:
        line = line.strip()
        if line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith(
                '4.') or line.startswith('5.'):
            # If there's already a question, save the previous question's data
            if question is not None and correct_answer is not None:
                trivia_data.append({
                    'question': question,
                    'posed_answers': posed_answers,
                    'correct_answer': correct_answer
                })

            # Start a new question
            question = line
            posed_answers = []
            correct_answer = None  # Reset correct_answer for the new question
        elif line.startswith('Answer:'):
            correct_answer = line.split('Answer:')[1].strip()
        else:
            posed_answers.append(line)

    # Add the last question
    if question is not None and correct_answer is not None:
        trivia_data.append({
            'question': question,
            'posed_answers': posed_answers,
            'correct_answer': correct_answer
        })

    return trivia_data


def ask_trivia_questions(trivia_data_list):
    """
    Asks a list of trivia questions, validates the user's answers, and tracks the score.
    """

    score = 0
    for trivia_data in trivia_data_list:
        print(f"{trivia_data['question']}\n")

        for answer in trivia_data['posed_answers']:
            print(answer)

        user_answer = input("\nYour answer (e.g., A, B, C): ").strip().upper()
        correct_answer_letter = trivia_data['correct_answer'].split(' ')[0]

        if user_answer in correct_answer_letter:
            print("Correct!\n")
            score += 1
        else:
            print(f"Sorry, that's incorrect. The correct answer was {trivia_data['correct_answer']}.\n")

    print(f"\nYour final score is {score}/{len(trivia_data_list)}\n")


def start_trivia(films):
    gpt_response = get_trivia(films)
    #print(f"GPT RESPONSE {gpt_response}")
    parsed_questions = parse_trivia_response(gpt_response)
    #print(f"PARSED QUESTIONS: {parsed_questions}")
    #ask_trivia_questions(parsed_questions)
    return parsed_questions

