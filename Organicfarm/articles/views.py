from .models import *
from .serializers import *
from core.models import *
from core.serializers import *
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated



class GetArticleView(APIView):
    def get(self, request, *args, **kwargs):
        article_id = kwargs.get('id')

        if article_id:
            try:
                article = Article.objects.get(id=article_id)
                category = article.category.all().values_list('id', flat=True)
                comments = ArticleComment.objects.filter(article=article)

                # Serialize the article data
                serializer = ArticlesSerializer(article)
                article_data = serializer.data
                article_data['category'] = list(category)
                article_data['comments'] = [
                    {'comment': comment.comment_field} for comment in comments]

                context = {'article': article_data}
                return render(request, 'articles/article_details.html', context)
            except Article.DoesNotExist:
                context = {'error': "No article found"}
                return render(request, 'articles/article_details.html', context, status=status.HTTP_404_NOT_FOUND)
        else:
            # Check if the user wants to see all articles
            show_all = request.GET.get('show_all', False)

            if show_all:
                # Fetch contact information
                info_obj = Contactinfo.objects.all()
                info_serializer = ContactinfoSerializer(
                    info_obj, many=True, context={'request': request}).data
                
                # Show all articles
                articles = Article.objects.all()
                articles_data = ArticlesSerializer(articles, many=True).data
                
                # show all category
                category = Articlescategory.objects.all()
                category_data = ArticlescategorySerializer(
                    category, many=True).data
                
                context = {
                    'info': info_serializer,
                    'articles': articles_data,
                    'categories': category_data,
                    }
                return render(request, 'articles/articles_page.html', context)
            

class ArticleByCategory(APIView):
    def get(self, request, category_id):
        try:
            category = Articlescategory.objects.get(id=category_id)
            articles = Article.objects.filter(category=category)
            serializer = ArticlesSerializer(articles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Articlescategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


class CreateComment(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, article_id):
        try:
            article = ArticleComment.objects.get(id=article_id)
        except ArticleComment.DoesNotExist:
            return Response({'error': "No article found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, article=article)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetComments(APIView):
    def get(self, request, article_id):
        try:
            article = ArticleComment.objects.get(id=article_id)
            comments = ArticleComment.objects.filter(article=article)
            serializer = ArticleCommentSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ArticleComment.DoesNotExist:
            return Response({'error': "No article found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateComment(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, comment_id):
        try:
            comment = ArticleComment.objects.get(id=comment_id)
            if comment.user.id != request.user.id:
                return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = ArticleCommentSerializer(
                comment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'error': "No comment found"}, status=status.HTTP_404_NOT_FOUND)


class DeleteComment(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        try:
            comment = ArticleComment.objects.get(id=comment_id)
            if comment.user.id == request.user.id:
                comment.delete()
                return Response({'msg': "comment Deleted"}, status=status.HTTP_200_OK)
            else:
                return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        except ObjectDoesNotExist:
            return Response({'error': "No comment found"}, status=status.HTTP_404_NOT_FOUND)


class CreateReplyComment(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, article_id, comment_id):
        try:
            parent_comment = ArticleComment.objects.get(id=comment_id)
            article = parent_comment.article
        except ArticleComment.DoesNotExist:
            return Response({'error': "No parent comment found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ArticleCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                user=request.user, article=article, parent=parent_comment
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetReplyComments(APIView):
    def get(self, request, article_id, comment_id):
        try:
            parent_comment = ArticleComment.objects.get(id=comment_id)
            reply_comments = parent_comment.get_children()
            serializer = ArticleCommentSerializer(reply_comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ArticleComment.DoesNotExist:
            return Response({'error': "No parent comment found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateReplyComment(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request, article_id, comment_id):
        try:
            comment = ArticleComment.objects.get(id=comment_id)
            if comment.user.id != request.user.id:
                return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            serializer = ArticleCommentSerializer(
                comment, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ArticleComment.DoesNotExist:
            return Response({'error': "No comment found"}, status=status.HTTP_404_NOT_FOUND)


class DeleteReplyComment(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, article_id, comment_id):
        try:
            comment = ArticleComment.objects.get(id=comment_id)
            if comment.user.id == request.user.id:
                comment.delete()
                return Response({'msg': "Comment deleted"}, status=status.HTTP_200_OK)
            else:
                return Response({'error': "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        except ArticleComment.DoesNotExist:
            return Response({'error': "No comment found"}, status=status.HTTP_404_NOT_FOUND)
