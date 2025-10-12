import speech_recognition as sr
from os import path

def transcricao (linkAudio):
    recognizer = sr.Recognizer()

    with sr.AudioFile(linkAudio) as source:
        audio = recognizer.record(source)
        
        try:
            return recognizer.recognize_google(audio, language="pt-BR")
        except sr.UnknownValueError:
            return "[Inaudível]"
        except sr.RequestError:
            return "[Erro de transcrição]"

def main():
    caminho = path.join(path.dirname(path.realpath(__file__)), r"C:\Users\osami\Downloads\english.wav")
    audio = sr.AudioData.from_file(caminho)
    texto = transcricao(caminho)
    print(texto)

if __name__ == "__main__":
    main()