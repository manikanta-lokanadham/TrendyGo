import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.contrib.auth.models import User
from products.models import Product, Category
from .models import UserBehavior, Recommendation, RecommendationItem, SimilarityMatrix
from django.db.models import Count, Sum, F, Q, Avg
from django.utils import timezone

class RecommendationEngine:
    def __init__(self):
        self.action_weights = {
            'V': 1.0,    # View
            'S': 1.5,    # Search
            'C': 3.0,    # Cart
            'W': 2.0,    # Wishlist
            'P': 5.0,    # Purchase
        }
    
    def generate_recommendations_for_user(self, user, method='H', limit=10):
        """Generate recommendations for a user using the specified method."""
        if method == 'CF':
            products = self.collaborative_filtering(user, limit)
        elif method == 'CB':
            products = self.content_based_filtering(user, limit)
        elif method == 'TR':
            products = self.trending_recommendations(limit)
        elif method == 'BR':
            products = self.recent_activity_based(user, limit)
        else:  # 'H' - Hybrid
            products = self.hybrid_recommendations(user, limit)
        
        # Create recommendation record
        recommendation = Recommendation.objects.create(user=user, method=method)
        
        # Create recommendation items
        for position, (product, score) in enumerate(products):
            RecommendationItem.objects.create(
                recommendation=recommendation,
                product=product,
                score=score,
                position=position + 1
            )
        
        return recommendation

    def collaborative_filtering(self, user, limit=10):
        """Collaborative filtering based on user-user similarity."""
        # Get all users with their behaviors
        user_behaviors = UserBehavior.objects.select_related('user', 'product')
        
        # If not enough data, fall back to content-based
        if user_behaviors.count() < 10:
            return self.content_based_filtering(user, limit)
        
        # Create user-item matrix 
        user_item_df = self._create_user_item_matrix(user_behaviors)
        
        # Find similar users
        similar_users = self._find_similar_users(user_item_df, user.id)
        
        if len(similar_users) == 0:
            return self.content_based_filtering(user, limit)
        
        # Get products that similar users have interacted with but current user hasn't
        recommended_products = self._get_similar_user_products(user, similar_users, user_item_df)
        
        # Return top N products
        return recommended_products[:limit]

    def content_based_filtering(self, user, limit=10):
        """Recommend products based on content similarity to user's past interactions."""
        try:
            # Get user's previous interactions
            user_interactions = UserBehavior.objects.filter(user=user)
            
            if not user_interactions.exists():
                return self.trending_recommendations(limit)
            
            # Get products user has interacted with and their weights
            user_products = {}
            for interaction in user_interactions:
                weight = interaction.count * self.action_weights.get(interaction.action, 1.0)
                user_products[interaction.product.id] = weight
            
            # Calculate weighted similarity scores for all products
            all_products = Product.objects.filter(is_available=True)
            product_scores = []
            
            for product in all_products:
                # Skip products user has already interacted with
                if product.id in user_products:
                    continue
                
                # Calculate similarity score
                similarity_score = 0
                
                for user_product_id, weight in user_products.items():
                    try:
                        user_product = Product.objects.get(id=user_product_id)
                        # Consider category and brand similarity
                        if product.category == user_product.category:
                            similarity_score += 0.3 * float(weight)
                        if product.brand and product.brand == user_product.brand:
                            similarity_score += 0.2 * float(weight)
                        
                        # Consider price range similarity (within 20% of price)
                        price_diff_ratio = abs(float(product.price) - float(user_product.price)) / max(float(product.price), float(user_product.price))
                        if price_diff_ratio < 0.2:
                            similarity_score += (1 - price_diff_ratio) * 0.1 * float(weight)
                        
                    except Product.DoesNotExist:
                        continue
                
                if similarity_score > 0:
                    product_scores.append((product, similarity_score))
            
            # Sort by similarity score
            product_scores.sort(key=lambda x: x[1], reverse=True)
            
            return product_scores[:limit]
        except Exception as e:
            print(f"Error in content-based filtering: {e}")
            return self.trending_recommendations(limit)

    def hybrid_recommendations(self, user, limit=10):
        """Combine collaborative and content-based filtering."""
        try:
            cf_products = dict(self.collaborative_filtering(user, limit * 2))
            cb_products = dict(self.content_based_filtering(user, limit * 2))
            
            # Merge scores, prioritizing products that appear in both lists
            product_scores = {}
            
            # Add collaborative filtering scores (0.6 weight)
            for product, score in cf_products.items():
                product_scores[product] = score * 0.6
            
            # Add content-based filtering scores (0.4 weight)
            for product, score in cb_products.items():
                if product in product_scores:
                    product_scores[product] += score * 0.4
                else:
                    product_scores[product] = score * 0.4
            
            # Sort by final score
            sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
            
            # If no recommendations, fall back to trending
            if not sorted_products:
                return self.trending_recommendations(limit)
            
            return sorted_products[:limit]
        except Exception as e:
            # Fallback to trending if there's an error
            print(f"Error in hybrid recommendations: {e}")
            return self.trending_recommendations(limit)

    def trending_recommendations(self, limit=10):
        """Recommend popular/trending products based on recent activity."""
        try:
            # Get recently popular products (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            
            popular_products = UserBehavior.objects.filter(
                created_at__gte=thirty_days_ago
            ).values('product').annotate(
                popularity=Sum('count')
            ).order_by('-popularity')[:limit]
            
            products = []
            for item in popular_products:
                try:
                    product = Product.objects.get(id=item['product'])
                    products.append((product, item['popularity']))
                except Product.DoesNotExist:
                    continue
            
            # If no user behaviors, return featured products
            if not products:
                featured_products = Product.objects.filter(is_featured=True, is_available=True)[:limit]
                products = [(product, 1.0) for product in featured_products]
            
            return products
        except Exception as e:
            # Fallback to featured products if there's an error
            print(f"Error in trending recommendations: {e}")
            featured_products = Product.objects.filter(is_featured=True, is_available=True)[:limit]
            return [(product, 1.0) for product in featured_products]

    def recent_activity_based(self, user, limit=10):
        """Recommend products based on user's recent activity."""
        # Get user's recent interactions
        recent_interactions = UserBehavior.objects.filter(
            user=user
        ).order_by('-updated_at')[:5]
        
        if not recent_interactions.exists():
            return self.trending_recommendations(limit)
        
        recent_products = []
        for interaction in recent_interactions:
            recent_products.append(interaction.product)
        
        # Find similar products to recent interactions
        similar_products = []
        for product in recent_products:
            # Find products in same category
            category_products = Product.objects.filter(
                category=product.category, 
                is_available=True
            ).exclude(id=product.id)
            
            # Find products from same brand
            if product.brand:
                brand_products = Product.objects.filter(
                    brand=product.brand, 
                    is_available=True
                ).exclude(id=product.id)
                
                for bp in brand_products:
                    if bp not in similar_products and bp not in recent_products:
                        similar_products.append((bp, 0.8))
            
            for cp in category_products:
                if cp not in recent_products and not any(p[0].id == cp.id for p in similar_products):
                    similar_products.append((cp, 0.6))
        
        similar_products.sort(key=lambda x: x[1], reverse=True)
        
        return similar_products[:limit]
    
    def _create_user_item_matrix(self, user_behaviors):
        """Create a user-item matrix from user behaviors."""
        data = []
        for behavior in user_behaviors:
            interaction_weight = behavior.count * self.action_weights.get(behavior.action, 1.0)
            data.append({
                'user_id': behavior.user.id,
                'product_id': behavior.product.id,
                'weight': interaction_weight
            })
        
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame()
        
        # Pivot to create user-item matrix
        user_item_matrix = df.pivot_table(
            index='user_id', 
            columns='product_id', 
            values='weight', 
            aggfunc='sum',
            fill_value=0
        )
        
        return user_item_matrix
    
    def _find_similar_users(self, user_item_df, user_id, top_n=5):
        """Find users with similar preferences."""
        if user_id not in user_item_df.index or user_item_df.empty:
            return []
        
        # Calculate user similarity
        user_similarity = cosine_similarity(user_item_df)
        user_similarity_df = pd.DataFrame(
            user_similarity,
            index=user_item_df.index,
            columns=user_item_df.index
        )
        
        # Get top similar users excluding the target user
        if user_id in user_similarity_df.index:
            similar_users = user_similarity_df[user_id].sort_values(ascending=False)[1:top_n+1]
            return similar_users.index.tolist()
        return []
    
    def _get_similar_user_products(self, user, similar_users, user_item_df):
        """Get products that similar users liked but target user hasn't interacted with."""
        if user_item_df.empty:
            return []
        
        user_id = user.id
        
        # Products user has already interacted with
        user_products = set()
        if user_id in user_item_df.index:
            user_row = user_item_df.loc[user_id]
            user_products = set(user_row[user_row > 0].index)
        
        # Collect weighted recommendations from similar users
        product_scores = {}
        
        for similar_user_id in similar_users:
            if similar_user_id not in user_item_df.index:
                continue
                
            similar_user_row = user_item_df.loc[similar_user_id]
            
            # Get products this similar user has interacted with
            similar_user_products = set(similar_user_row[similar_user_row > 0].index)
            
            # Recommend products the target user hasn't interacted with
            new_products = similar_user_products - user_products
            
            for product_id in new_products:
                score = similar_user_row[product_id]
                if product_id in product_scores:
                    product_scores[product_id] += score
                else:
                    product_scores[product_id] = score
        
        # Convert to list of (product, score) tuples and sort by score
        product_score_list = []
        for product_id, score in product_scores.items():
            try:
                product = Product.objects.get(id=product_id)
                product_score_list.append((product, score))
            except Product.DoesNotExist:
                continue
        
        product_score_list.sort(key=lambda x: x[1], reverse=True)
        
        return product_score_list
    
    def update_content_similarity_matrices(self):
        """Calculate and store content similarity matrices for all products."""
        products = Product.objects.filter(is_available=True)
        
        # Create product feature vectors
        product_data = []
        
        for product in products:
            # Combine important product features into a text representation
            features = [
                product.name,
                product.description,
                product.category.name,
                product.brand.name if product.brand else ""
            ]
            feature_text = " ".join([str(f) for f in features if f])
            
            product_data.append({
                'id': product.id,
                'features': feature_text
            })
        
        if not product_data:
            return
        
        # Create a TF-IDF vectorizer
        df = pd.DataFrame(product_data)
        tfidf = TfidfVectorizer(stop_words='english')
        
        # Create TF-IDF matrix
        tfidf_matrix = tfidf.fit_transform(df['features'])
        
        # Calculate cosine similarity between products
        cosine_sim = cosine_similarity(tfidf_matrix)
        
        # Store similarity matrices for each product
        for i, product_id in enumerate(df['id']):
            try:
                product = Product.objects.get(id=product_id)
                similarity_data, created = SimilarityMatrix.objects.get_or_create(product=product)
                similarity_data.set_matrix(cosine_sim[i])
                similarity_data.save()
            except Product.DoesNotExist:
                continue
        
        return True 

    def content_based_similarity(self, product, limit=10):
        """Find products similar to the given product."""
        try:
            # Get all available products except the current one
            all_products = Product.objects.filter(is_available=True).exclude(id=product.id)
            
            # Calculate similarity scores
            product_scores = []
            
            for other_product in all_products:
                # Calculate similarity score
                similarity_score = 0
                
                # Consider category and brand similarity
                if product.category == other_product.category:
                    similarity_score += 0.3
                if product.brand and product.brand == other_product.brand:
                    similarity_score += 0.2
                
                # Consider price range similarity (within 20% of price)
                price_diff_ratio = abs(float(product.price) - float(other_product.price)) / max(float(product.price), float(other_product.price))
                if price_diff_ratio < 0.2:
                    similarity_score += (1 - price_diff_ratio) * 0.1
                
                if similarity_score > 0:
                    product_scores.append((other_product, similarity_score))
            
            # Sort by similarity score
            product_scores.sort(key=lambda x: x[1], reverse=True)
            
            return product_scores[:limit]
        except Exception as e:
            print(f"Error in content-based similarity: {e}")
            # Fallback to products in the same category
            return [(p, 1.0) for p in Product.objects.filter(
                category=product.category, 
                is_available=True
            ).exclude(id=product.id)[:limit]] 

    def get_recommendations(self, user, limit=8):
        """Get product recommendations for a user"""
        try:
            # If user is authenticated, try to get personalized recommendations
            if user.is_authenticated:
                # Get user's viewed/purchased products categories
                user_categories = set()
                for behavior in user.userbehavior_set.all():
                    user_categories.add(behavior.product.category_id)
                
                if user_categories:
                    # Get products from categories the user has shown interest in
                    recommended = Product.objects.filter(
                        category_id__in=user_categories,
                        is_available=True
                    ).exclude(
                        userbehavior__user=user  # Exclude products user has already interacted with
                    ).order_by('-rating', '-created_at')[:limit]
                    
                    if recommended:
                        return recommended
            
            # Fallback to top-rated products if no personalized recommendations
            return Product.objects.filter(
                is_available=True,
                rating__gt=0
            ).order_by('-rating', '-created_at')[:limit]
            
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            # Return featured products as a fallback
            return Product.objects.filter(is_featured=True)[:limit] 