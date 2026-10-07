import { useEffect, useState } from 'react';
import { useUser } from '../../context/UserContext';
import { Sparkles, TrendingUp, Target, BookOpen } from 'lucide-react';

export default function HomePage() {
  const { userData } = useUser();
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) {
      setGreeting('Good Morning');
    } else if (hour < 18) {
      setGreeting('Good Afternoon');
    } else {
      setGreeting('Good Evening');
    }
  }, []);

  return (
    <div className="max-w-6xl mx-auto">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 rounded-2xl p-8 mb-8 shadow-lg transition-colors duration-300">
        <div className="flex items-center gap-3 mb-3">
          <Sparkles className="w-8 h-8 text-yellow-300" />
          <h1 className="text-3xl font-bold text-white">
            {greeting}, {userData.profile.name || 'User'}!
          </h1>
        </div>
        <p className="text-blue-100 text-lg">
          Welcome to your personalized career dashboard
        </p>
      </div>

      {/* Services Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">What We Offer</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700">
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg w-fit mb-4">
              <BookOpen className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Personalized Learning Path
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Get a customized roadmap based on your syllabus and career goals. Upload your materials 
              and let our AI create the perfect study plan for you.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700">
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg w-fit mb-4">
              <TrendingUp className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Skill Development
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Receive intelligent recommendations on which technologies and skills to learn based on 
              your current expertise and market demands.
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg w-fit mb-4">
              <Target className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Career Opportunities
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Access curated job listings, internship opportunities, and company matches that align 
              with your skills and career aspirations.
            </p>
          </div>
        </div>
      </div>

      {/* Student Features */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 mb-8 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Student Features</h2>
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">1</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Upload Your Syllabus</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Share your course syllabus and we'll analyze it to create a comprehensive learning roadmap 
                tailored to your academic requirements.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">2</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Get Technology Recommendations</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Based on your syllabus content, receive smart suggestions on complementary technologies. 
                For example, if you're learning Java, we'll recommend React for frontend and Spring Boot for frameworks.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">3</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Access Learning Videos</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Find role-relevant YouTube tutorials for your selected career path and skills.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">4</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Find Internships</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Discover internship opportunities from various companies and institutes that match 
                your skill set and learning path.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Job Seeker Features */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Job Seeker Features</h2>
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">1</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Upload Your Resume</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Share your resume and professional details to get matched with relevant job opportunities 
                and career advancement suggestions.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">2</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Discover Job Roles</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Get personalized job role recommendations based on your skills, experience, and career goals.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">3</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Find Hiring Companies</h3>
              <p className="text-gray-600 dark:text-gray-300">
                See which companies are actively hiring for positions that match your skill set and preferences.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold">4</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Skill Enhancement Suggestions</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Receive recommendations on additional skills to learn that will make you more competitive 
                and open up new career opportunities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
