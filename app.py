import streamlit as st
import pandas as pd
import hashlib
import os

# CSV 파일 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("movie_data.csv", encoding='cp949')
        df.columns = df.columns.str.strip().str.lower()  # 컬럼명 공백 제거 및 소문자화
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

def save_users(users):
    pd.DataFrame(users).to_csv("movie_users.csv", index=False, encoding='cp949')

def load_users():
    path = "movie_users.csv"
    if os.path.exists(path):
        return pd.read_csv(path, encoding='cp949').to_dict('records')
    return []

def save_ratings(ratings):
    pd.DataFrame(ratings).to_csv("movie_ratings.csv", index=False, encoding='cp949')

def load_ratings():
    path = "movie_ratings.csv"
    if os.path.exists(path):
        return pd.read_csv(path, encoding='cp949').to_dict('records')
    return []

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    st.set_page_config(page_title="영화 추천 시스템", layout="wide")
    st.title("🎬 영화 추천 및 검색 시스템")

    df = load_data()
    users = load_users()
    ratings = load_ratings()

    if 'user' not in st.session_state:
        st.session_state.user = None
        st.session_state.role = None

    # 포스터 파일 폴더 경로
    poster_folder = "poster_file"

    # 사이드바 사용자 인증
    with st.sidebar:
        st.header("👤 사용자 인증")
        if st.session_state.user:
            st.write(f"환영합니다, **{st.session_state.user}님!**")
            if st.button("로그아웃"):
                st.session_state.user = None
                st.session_state.role = None
                st.success("로그아웃 성공!")
        else:
            choice = st.radio("로그인/회원가입", ["로그인", "회원가입"])
            if choice == "로그인":
                username = st.text_input("사용자명")
                password = st.text_input("비밀번호", type="password")
                if st.button("로그인"):
                    user = next((u for u in users if u['username'] == username and u['password'] == hash_password(password)), None)
                    if user:
                        st.session_state.user = username
                        st.session_state.role = user['role']
                        st.success("로그인 성공!")
                    else:
                        st.error("잘못된 사용자명 또는 비밀번호입니다.")
            else:
                new_username = st.text_input("새 사용자명")
                new_password = st.text_input("새 비밀번호", type="password")
                if st.button("회원가입"):
                    if any(u['username'] == new_username for u in users):
                        st.error("이미 존재하는 사용자명입니다.")
                    else:
                        users.append({'username': new_username, 'password': hash_password(new_password), 'role': 'user'})
                        save_users(users)
                        st.success("회원가입 성공! 이제 로그인할 수 있습니다.")

    st.markdown("---")

    # 메인 영역
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 영화 검색", "⭐ 추천 영화", "📈 나의 활동", "🔧 사용자 계정 관리", "👑 관리자 보기"])

    # 영화 검색
    with tab1:
        st.header("🎥 영화 검색")
        search_term = st.text_input("🔍 검색", placeholder="영화 제목을 입력하세요...")
        genre_filter = st.selectbox("🎭 장르 필터", options=["모든 장르"] + df['genre'].unique().tolist())

        # 필터링 및 페이지네이션
        filtered_df = df[df['title'].str.contains(search_term, case=False)]
        if genre_filter != "모든 장르":
            filtered_df = filtered_df[filtered_df['genre'] == genre_filter]

        total_movies = len(filtered_df)
        if total_movies == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            page_size = 5
            total_pages = (total_movies // page_size) + (1 if total_movies % page_size != 0 else 0)
            page = st.number_input("페이지 번호", min_value=1, max_value=total_pages, value=1)

            start_idx = (page - 1) * page_size
            end_idx = min(page * page_size, total_movies)

            for _, movie in filtered_df.iloc[start_idx:end_idx].iterrows():
                st.subheader(movie['title'])

                # 포스터 파일 경로
                poster_path = os.path.join(poster_folder, movie.get('poster_file', ''))
                if os.path.exists(poster_path) and pd.notna(movie.get('poster_file')):
                    st.image(poster_path, width=200)  # 이미지 표시
                else:
                    st.write("포스터 이미지가 없습니다.")  # 이미지가 없을 경우 메시지 출력

                # 영화 정보 출력
                st.write(f"**영화 ID**: {movie['movie_id']}")
                st.write(f"**제작사**: {movie['distributor']}")
                st.write(f"**감독**: {movie['director']}")
                st.write(f"**배우**: {movie['actor']}")
                st.write(f"**장르**: {movie['genre']}")
                st.write(f"**개봉일**: {movie['release_date']}")

                running_time = movie.get('running_time', '정보 없음')
                if running_time != '정보 없음':
                    try:
                        running_time = int(running_time)
                        st.write(f"**상영 시간**: {running_time}분")
                    except ValueError:
                        st.write("**상영 시간**: 정보 없음")
                else:
                    st.write(f"**상영 시간**: {running_time}분")

                st.write(f"**영화 평점**: {movie['rating']}")
                st.write(f"**현재 상태**: {movie['running_state']}")
                st.markdown("---")

                # 영화에 대한 평점 표시
                movie_ratings = [r['rating'] for r in ratings if r['movie'] == movie['title']]
                if movie_ratings:
                    avg_rating = round(sum(movie_ratings) / len(movie_ratings), 2)
                    st.write(f"사이트 평점: {'⭐' * int(avg_rating)} ({avg_rating}/10)")
                else:
                    st.write("아직 평점이 없습니다.")

                movie_reviews = [r['review'] for r in ratings if r['movie'] == movie['title'] and r.get('review') is not None]
                if movie_reviews:
                    st.write("리뷰:")
                    for review in movie_reviews:
                        st.write(f"- {review}")
                else:
                    st.write("아직 리뷰가 없습니다.")

                if st.session_state.user:
                    if any(r['username'] == st.session_state.user and r['movie'] == movie['title'] for r in ratings):
                        st.info("이미 이 영화에 평점과 리뷰를 남겼습니다.")
                    else:
                        rating = st.number_input(f"평점을 선택하세요 ({movie['title']})", min_value=0.0, max_value=10.0, step=0.1, format="%.2f")
                        review = st.text_area(f"리뷰를 작성하세요 ({movie['title']})", placeholder="영화를 보고 느낀 점을 적어보세요...")

                        if st.button(f"'{movie['title']}' 평점 및 리뷰 남기기", key=f"rate-review-{movie['title']}"):
                            ratings.append({
                                'username': st.session_state.user, 
                                'movie': movie['title'], 
                                'rating': round(rating, 2),
                                'review': review if review else None
                            })
                            save_ratings(ratings)
                            st.success("평점과 리뷰가 저장되었습니다.")

    # 추천 영화
    with tab2:
        st.header("⭐ 추천 영화")
        if st.session_state.user:
            user_ratings = [r for r in ratings if r['username'] == st.session_state.user]
            if user_ratings:
                favorite_genres = [df[df['title'] == r['movie']].iloc[0]['genre'] for r in user_ratings if not df[df['title'] == r['movie']].empty]
                recommended_movies = df[df['genre'].isin(favorite_genres) & ~df['title'].isin([r['movie'] for r in user_ratings])]
                
                sort_by = st.radio("추천 영화 정렬 기준", ["가장 평점 높은 순", "리뷰가 많은 순", "사이트 평점 순"])
                
                if sort_by == "가장 평점 높은 순":
                    recommended_movies = recommended_movies.sort_values(by='rating', ascending=False)
                elif sort_by == "리뷰가 많은 순":
                    movie_reviews_count = {movie: len([r for r in ratings if r['movie'] == movie]) for movie in recommended_movies['title']}
                    recommended_movies['review_count'] = recommended_movies['title'].map(movie_reviews_count)
                    recommended_movies = recommended_movies.sort_values(by='review_count', ascending=False)
                else:
                    movie_avg_rating = {movie: round(sum([r['rating'] for r in ratings if r['movie'] == movie]) / len([r for r in ratings if r['movie'] == movie]), 2) for movie in recommended_movies['title']}
                    recommended_movies['avg_rating'] = recommended_movies['title'].map(movie_avg_rating)
                    recommended_movies = recommended_movies.sort_values(by='avg_rating', ascending=False)

                st.write("추천 영화 목록:")
                for _, movie in recommended_movies.iterrows():
                    st.subheader(movie['title'])
                    st.write(f"장르: {movie['genre']}, 평점: {movie['rating']}")
                    
                    poster_path = os.path.join(poster_folder, movie.get('poster_file', ''))
                    if os.path.exists(poster_path):
                        st.image(poster_path, width=200)  # 추천 영화 이미지 표시
                    else:
                        st.write("포스터 이미지가 없습니다.")
            else:
                st.warning("추천 영화를 보기 위해 먼저 영화를 평가해주세요.")
        else:
            st.warning("로그인 후 추천 영화를 볼 수 있습니다.")

    # 나의 활동
    with tab3:
        st.header("📈 나의 활동")
        if st.session_state.user:
            user_ratings = [r for r in ratings if r['username'] == st.session_state.user]
            if user_ratings:
                for r in user_ratings:
                    st.write(f"영화: {r['movie']}, 평점: {r['rating']}")
                    if r.get('review'):
                        st.write(f"리뷰: {r['review']}")
                    st.markdown("---")
            else:
                st.write("평가한 영화가 없습니다. 영화 검색 후 평점을 남겨보세요.")
        else:
            st.warning("로그인 후 나의 활동을 확인할 수 있습니다.")

    # 사용자 계정 관리
    with tab4:
        st.header("🔧 사용자 계정 관리")
        if st.session_state.user:
            user = next(u for u in users if u['username'] == st.session_state.user)
            st.write(f"사용자명: {user['username']}")
            st.write(f"역할: {user['role']}")
            if st.button("비밀번호 변경"):
                new_password = st.text_input("새 비밀번호", type="password")
                user['password'] = hash_password(new_password)
                save_users(users)
                st.success("비밀번호가 변경되었습니다.")
        else:
            st.warning("로그인 후 계정 관리가 가능합니다.")

    # 관리자 보기 (관리자 전용)
    with tab5:
        st.header("👑 관리자 보기")
        if st.session_state.role == 'admin':
            st.subheader("전체 사용자 목록")
            for user in users:
                st.write(f"**사용자명**: {user['username']} | **역할**: {user['role']}")
            st.markdown("---")
        
            st.subheader("전체 영화 평점 목록")
            # 평가 목록을 보기 좋게 표시
            rating_data = []
            for movie in df['title']:
                movie_ratings = [r for r in ratings if r['movie'] == movie]
                if movie_ratings:
                    avg_rating = round(sum(r['rating'] for r in movie_ratings) / len(movie_ratings), 2)
                    rating_data.append({
                        "영화 제목": movie,
                        "평균 평점": avg_rating,
                        "평점 수": len(movie_ratings),
                        "리뷰": ", ".join([r['review'] if r['review'] else "리뷰 없음" for r in movie_ratings])
                    })
        
            if rating_data:
                rating_df = pd.DataFrame(rating_data)
                st.table(rating_df)  # 테이블 형식으로 평가 목록 출력
            else:
                st.write("평가된 영화가 없습니다.")
        
            st.markdown("---")
        
            # 리뷰 수정 기능 추가
            st.subheader("리뷰 수정")
            movie_to_edit = st.selectbox("수정할 영화 선택", [movie for movie in df['title']])
            reviews_to_edit = [r for r in ratings if r['movie'] == movie_to_edit]
        
            if reviews_to_edit:
                review_data = []
                for review in reviews_to_edit:
                    review_data.append({
                        "사용자명": review['username'],
                        "평점": review['rating'],
                        "리뷰": review['review']
                    })
            
                review_df = pd.DataFrame(review_data)
                st.table(review_df)  # 선택된 영화에 대한 리뷰 테이블 표시

                selected_user = st.selectbox("수정할 리뷰의 사용자 선택", [r['username'] for r in reviews_to_edit])
                review_to_edit = next(r for r in reviews_to_edit if r['username'] == selected_user)
            
                new_review = st.text_area(f"{selected_user}의 리뷰 수정", value=review_to_edit['review'])
            
                if st.button(f"{selected_user}의 리뷰 수정 완료"):
                    review_to_edit['review'] = new_review
                    save_ratings(ratings)
                    st.success(f"'{selected_user}'의 리뷰가 수정되었습니다.")
            else:
                st.write("선택한 영화에 대한 리뷰가 없습니다.")
        else:
            st.info("관리자만 접근할 수 있습니다.")


if __name__ == "__main__":
    main()
