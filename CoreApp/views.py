from PyPDF2 import PdfReader
import os
import openai

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.conf import settings

from CoreApp.serializers import KnowledgeDocumentSerializer,AskQuestionSerializer
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter

embedding_model = OpenAIEmbeddings()
VECTOR_STORE_PATH = "vector_store"


class UploadKnowledgeBase(APIView):
    parser_classes = [MultiPartParser]

    def extract_content(self, path, ext):
        try:
            if ext == ".pdf":
                reader = PdfReader(path)
                return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
            elif ext == ".md":
                with open(path, 'r', encoding="utf-8") as f:
                    return f.read()
            elif ext == ".txt":
                with open(path, 'r', encoding="utf-8") as f:
                    return f.read()
            else:
                return ""
        except Exception as e:
            print(f"Error reading file: {e}")
            return ""

    def post(self, request):
        serializer = KnowledgeDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        instance = serializer.save()

        ext = os.path.splitext(instance.file.name)[1].lower()
        content = self.extract_content(instance.file.path, ext)

        if not content.strip():
            return Response({"error": "Could not extract any content from the file."}, status=400)

        chunks = CharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_text(content)
        vectordb = FAISS.from_texts(chunks, embedding_model)
        vectordb.save_local(VECTOR_STORE_PATH)

        return Response({"message": "Document uploaded and processed."}, status=201)



class AskQuestionView(APIView):
    def post(self, request):
        serializer = AskQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        question = serializer.validated_data['question']

        try:
            vectordb = FAISS.load_local(VECTOR_STORE_PATH, embedding_model)
        except Exception:
            return Response({"error": "Vector store not found. Please upload a document first."}, status=404)

        docs = vectordb.similarity_search(question, k=3)
        context = "\n".join([doc.page_content for doc in docs])

        prompt = f"""Use the context below to answer the question:
        Context: {context}
        Question: {question}
        Answer:"""

        openai.api_key = settings.OPENAI_API_KEY
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            return Response({"error": "Failed to fetch response from OpenAI.", "details": str(e)}, status=500)

        return Response({
            "answer": answer,
            "sources": ["LocalVectorStore"]
        })


# class AskQuestionView(APIView):
#     def post(self, request):
#         serializer = AskQuestionSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=400)
#
#         question = serializer.validated_data['question']
#
#         prompt = f"Answer this question:\n{question}"  # Simplified prompt
#
#         openai.api_key = settings.OPENAI_API_KEY
#         try:
#             response = openai.ChatCompletion.create(
#                 model="gpt-4.1",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.3
#             )
#             answer = response.choices[0].message.content.strip()
#         except Exception as e:
#             return Response({"error": "Failed to fetch response from OpenAI.", "details": str(e)}, status=500)
#
#         return Response({
#             "answer": answer,
#             "sources": ["OpenAI Direct"]
#         })
