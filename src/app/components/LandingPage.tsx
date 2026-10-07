import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, Briefcase, Target, TrendingUp, Users, Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { useTheme } from '../context/ThemeContext';

export default function LandingPage() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [showGetStarted, setShowGetStarted] = useState(false);

  const handleGetStarted = () => {
    setShowGetStarted(true);
    setTimeout(() => {
      const element = document.getElementById('get-started-section');
      element?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 transition-colors duration-300">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shadow-md transition-colors duration-300">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <h1 className="font-bold text-2xl text-gray-900 dark:text-white">CareerAlign</h1>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 text-center">
        <h2 className="text-5xl font-bold mb-6 text-gray-900 dark:text-white">
          Your Journey to Success Starts Here
        </h2>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-12 max-w-3xl mx-auto">
          CareerAlign is your all-in-one platform for academic excellence and career advancement. 
          Whether you're a student planning your future or a job seeker ready to take the next step, 
          we've got you covered.
        </p>
        <Button
          onClick={handleGetStarted}
          size="lg"
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg shadow-lg hover:shadow-xl transition-all duration-300"
        >
          Get Started <ArrowRight className="ml-2 w-5 h-5" />
        </Button>
      </section>

      {/* Features Section with Images */}
      <section className="container mx-auto px-6 py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center mb-20">
          <div className="order-2 md:order-1">
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1758270705183-cf829539e436?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdHVkZW50cyUyMHN0dWR5aW5nJTIwY2FyZWVyJTIwZGV2ZWxvcG1lbnR8ZW58MXx8fHwxNzcwMjY4NzgxfDA&ixlib=rb-4.1.0&q=80&w=1080"
              alt="Students studying"
              className="rounded-2xl shadow-2xl w-full h-[400px] object-cover hover:scale-105 transition-transform duration-300"
            />
          </div>
          <div className="order-1 md:order-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <BookOpen className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900 dark:text-white">For Students</h3>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-300 mb-4">
              Upload your syllabus and let our AI-powered platform create a personalized roadmap for your academic journey.
            </p>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">1</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Upload your syllabus and resume</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">2</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Get personalized learning roadmaps</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">3</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Access curated learning videos and resources</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-purple-600 dark:bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">4</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Discover relevant internship opportunities</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg">
                <Briefcase className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900 dark:text-white">For Job Seekers</h3>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-300 mb-4">
              Find the perfect job that matches your skills and career aspirations with our intelligent matching system.
            </p>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">1</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Upload your resume and professional details</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">2</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Get matched with relevant job roles</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">3</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Discover companies actively hiring for your skills</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-600 dark:bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-white text-sm font-bold">4</span>
                </div>
                <span className="text-gray-700 dark:text-gray-300">Receive recommendations for skill enhancement</span>
              </li>
            </ul>
          </div>
          <div>
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1758520144426-edf40a58f299?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxqb2IlMjBpbnRlcnZpZXclMjBwcm9mZXNzaW9uYWwlMjB3b3JrcGxhY2V8ZW58MXx8fHwxNzcwMjY4NzgxfDA&ixlib=rb-4.1.0&q=80&w=1080"
              alt="Job interview"
              className="rounded-2xl shadow-2xl w-full h-[400px] object-cover hover:scale-105 transition-transform duration-300"
            />
          </div>
        </div>
      </section>

      {/* Why Choose Us Section */}
      <section className="bg-blue-600 dark:bg-blue-800 py-20 transition-colors duration-300">
        <div className="container mx-auto px-6">
          <h3 className="text-4xl font-bold text-center text-white mb-16">Why Choose CareerAlign?</h3>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
              <div className="p-4 bg-orange-100 dark:bg-orange-900 rounded-lg w-fit mb-4">
                <TrendingUp className="w-10 h-10 text-orange-600 dark:text-orange-400" />
              </div>
              <h4 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">AI-Powered Insights</h4>
              <p className="text-gray-600 dark:text-gray-300">
                Our intelligent system analyzes your profile to provide personalized recommendations 
                and career guidance tailored to your unique skills and goals.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
              <div className="p-4 bg-pink-100 dark:bg-pink-900 rounded-lg w-fit mb-4">
                <Users className="w-10 h-10 text-pink-600 dark:text-pink-400" />
              </div>
              <h4 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">Community Support</h4>
              <p className="text-gray-600 dark:text-gray-300">
                Join thousands of students and professionals who are already using CareerAlign 
                to achieve their career goals and academic excellence.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
              <div className="p-4 bg-teal-100 dark:bg-teal-900 rounded-lg w-fit mb-4">
                <Target className="w-10 h-10 text-teal-600 dark:text-teal-400" />
              </div>
              <h4 className="text-2xl font-bold mb-3 text-gray-900 dark:text-white">Goal-Oriented</h4>
              <p className="text-gray-600 dark:text-gray-300">
                Set clear goals and track your progress with our comprehensive dashboard. 
                Stay motivated and focused on what matters most to your career.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Success Stories Section */}
      <section className="container mx-auto px-6 py-20">
        <h3 className="text-4xl font-bold text-center text-gray-900 dark:text-white mb-16">Success in Action</h3>
        <div className="grid md:grid-cols-2 gap-8">
          <div className="relative">
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1739298061740-5ed03045b280?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0ZWFtJTIwY29sbGFib3JhdGlvbiUyMHdvcmtzcGFjZXxlbnwxfHx8fDE3NzAyMzM1NjJ8MA&ixlib=rb-4.1.0&q=80&w=1080"
              alt="Team collaboration"
              className="rounded-2xl shadow-xl w-full h-[300px] object-cover"
            />
            <div className="absolute bottom-4 left-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-4 rounded-lg">
              <p className="text-gray-900 dark:text-white font-semibold">Collaborative Learning</p>
              <p className="text-sm text-gray-600 dark:text-gray-300">Connect with peers and mentors</p>
            </div>
          </div>
          <div className="relative">
            <ImageWithFallback
              src="https://images.unsplash.com/photo-1758518729240-7162d07427b8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjYXJlZXIlMjBzdWNjZXNzJTIwZ3Jvd3RofGVufDF8fHx8MTc3MDIwMTc3MXww&ixlib=rb-4.1.0&q=80&w=1080"
              alt="Career success"
              className="rounded-2xl shadow-xl w-full h-[300px] object-cover"
            />
            <div className="absolute bottom-4 left-4 right-4 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-4 rounded-lg">
              <p className="text-gray-900 dark:text-white font-semibold">Career Growth</p>
              <p className="text-sm text-gray-600 dark:text-gray-300">Achieve your professional dreams</p>
            </div>
          </div>
        </div>
      </section>

      {/* Get Started Section */}
      {showGetStarted && (
        <section id="get-started-section" className="bg-gray-50 dark:bg-gray-900 py-20 transition-colors duration-300">
          <div className="container mx-auto px-6">
            <div className="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-12 text-center">
              <h3 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Choose Your Path</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-8">
                Select the option that best describes you to get started on your journey
              </p>
              <div className="grid md:grid-cols-2 gap-6">
                <Button
                  onClick={() => navigate('/auth/student')}
                  className="bg-purple-600 hover:bg-purple-700 text-white py-8 text-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                >
                  <div className="flex flex-col items-center gap-2">
                    <BookOpen className="w-8 h-8" />
                    <span>Start as a Student</span>
                  </div>
                </Button>
                <Button
                  onClick={() => navigate('/auth/job-seeker')}
                  className="bg-green-600 hover:bg-green-700 text-white py-8 text-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
                >
                  <div className="flex flex-col items-center gap-2">
                    <Briefcase className="w-8 h-8" />
                    <span>Start as a Job Seeker</span>
                  </div>
                </Button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="bg-gray-900 dark:bg-black text-white py-12 transition-colors duration-300">
        <div className="container mx-auto px-6 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Target className="w-6 h-6 text-blue-400" />
            <p className="font-semibold text-xl">CareerAlign</p>
          </div>
          <p className="text-gray-400">
            Empowering students and professionals to achieve their dreams
          </p>
          <p className="text-gray-500 mt-4 text-sm">© 2026 CareerAlign. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
