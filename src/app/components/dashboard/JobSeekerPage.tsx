import { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Briefcase, Building2, Lightbulb, Plus, Edit2, ArrowLeft, FileText, Eye, X, File as FileIcon, ExternalLink, MapPin, Clock, Search, RefreshCw, Loader2, TrendingUp, Target, Github, Award, BookOpen, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import {
  analyzeGitHubProfile,
  analyzeSkillGap,
  apiErrorMessage,
  createStudentSkillTwin,
  extractSkills,
  getCareerAlignment,
  listCareerRoles,
  makeSelfDeclaredEvidence,
  matchJobs,
  predictRole,
  searchJobs,
  type CareerAlignmentResponse,
  type JobMatch,
  type RolePrediction,
  type SearchedJob,
  type SkillGapResponse,
  type StudentEvidenceInput,
} from '../../api';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useUser } from '../../context/UserContext';
import { toast } from 'sonner';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import SkillChip from '../ui/SkillChip';

export default function JobSeekerPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { userData, updateJobSeekerSkills, updateJobSeekerDetails } = useUser();
  const [newSkill, setNewSkill] = useState('');
  const [isViewingResume, setIsViewingResume] = useState(false);
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  const [details, setDetails] = useState({
    marks10th: userData.marks10th,
    marks12th: userData.marks12th,
    cgpa: userData.cgpa,
    linkedinProfile: userData.linkedinProfile,
    githubLink: userData.githubLink,
  });

  const addSkill = () => {
    if (newSkill.trim()) {
      const updatedSkills = [...userData.jobSeekerSkills, newSkill.trim()];
      updateJobSeekerSkills(updatedSkills);
      setNewSkill('');
      toast.success('Skill added!');
    }
  };

  const saveDetails = () => {
    updateJobSeekerDetails(details);
    setIsEditingDetails(false);
    toast.success('Details updated!');
  };

  if (location.pathname === '/dashboard/job-seeker') {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Job Seeker Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Find the perfect job that matches your skills and aspirations
          </p>
        </div>

        {/* Skills Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Your Skills</h2>
          <div className="mb-4">
            {userData.jobSeekerSkills.length > 0 || userData.profile.skills.length > 0 ? (
              <div className="mb-4 flex flex-wrap gap-2">
                {[...new Set([...userData.profile.skills, ...userData.jobSeekerSkills])].map((skill) => (
                  <SkillChip key={skill} tone="green">{skill}</SkillChip>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 mb-4">No skills added yet</p>
            )}
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                placeholder="Add a skill (e.g., JavaScript, Project Management)"
                className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                onKeyPress={(e) => e.key === 'Enter' && addSkill()}
              />
              <Button onClick={addSkill} className="bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                Add
              </Button>
            </div>
          </div>
        </div>

        {/* Resume Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Your Resume</h2>
          {userData.resume ? (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <p className="text-gray-700 dark:text-gray-300 font-medium">{userData.resume.fileName}</p>
              </div>
              <Button
                onClick={() => setIsViewingResume(true)}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <Eye className="w-4 h-4 mr-2" />
                View Resume
              </Button>

              {/* View Resume Modal */}
              {isViewingResume && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
                    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{userData.resume.fileName}</h3>
                      </div>
                      <button
                        onClick={() => setIsViewingResume(false)}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                      >
                        <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                      </button>
                    </div>
                    <div className="flex-1 overflow-auto p-4">
                      {userData.resume.content.startsWith('data:application/pdf') ? (
                        <iframe
                          src={userData.resume.content}
                          className="w-full h-[70vh] rounded-lg border border-gray-200 dark:border-gray-700"
                          title="Resume Preview"
                        />
                      ) : userData.resume.content.startsWith('data:image/') ? (
                        <img
                          src={userData.resume.content}
                          alt="Resume"
                          className="max-w-full mx-auto rounded-lg"
                        />
                      ) : (
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 max-h-[70vh] overflow-y-auto">
                          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono text-sm">
                            {atob(userData.resume.content.split(',')[1] || '')}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No resume uploaded yet. Go to the Resume section to upload one.
            </p>
          )}
        </div>

        {/* Academic & Professional Details */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 mb-6 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Academic & Professional Details</h2>
            {!isEditingDetails && (
              <Button
                onClick={() => setIsEditingDetails(true)}
                variant="outline"
                size="sm"
                className="border-2"
              >
                <Edit2 className="w-4 h-4 mr-2" />
                Edit
              </Button>
            )}
          </div>
          {isEditingDetails ? (
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-700 dark:text-gray-300">10th Grade Marks (%)</Label>
                  <Input
                    type="text"
                    value={details.marks10th}
                    onChange={(e) => setDetails({ ...details, marks10th: e.target.value })}
                    placeholder="e.g., 85%"
                    className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                  />
                </div>
                <div>
                  <Label className="text-gray-700 dark:text-gray-300">12th Grade Marks (%)</Label>
                  <Input
                    type="text"
                    value={details.marks12th}
                    onChange={(e) => setDetails({ ...details, marks12th: e.target.value })}
                    placeholder="e.g., 90%"
                    className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                  />
                </div>
                <div>
                  <Label className="text-gray-700 dark:text-gray-300">CGPA (out of 10)</Label>
                  <Input
                    type="text"
                    value={details.cgpa}
                    onChange={(e) => setDetails({ ...details, cgpa: e.target.value })}
                    placeholder="e.g., 7.5"
                    className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                  />
                </div>
              </div>
              <div>
                <Label className="text-gray-700 dark:text-gray-300">LinkedIn Profile</Label>
                <Input
                  type="url"
                  value={details.linkedinProfile}
                  onChange={(e) => setDetails({ ...details, linkedinProfile: e.target.value })}
                  placeholder="https://linkedin.com/in/yourprofile"
                  className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                />
              </div>
              <div>
                <Label className="text-gray-700 dark:text-gray-300">GitHub Profile</Label>
                <Input
                  type="url"
                  value={details.githubLink}
                  onChange={(e) => setDetails({ ...details, githubLink: e.target.value })}
                  placeholder="https://github.com/yourusername"
                  className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                />
              </div>
              <div className="flex gap-2 mt-4">
                <Button onClick={saveDetails} className="bg-green-600 hover:bg-green-700">
                  Save
                </Button>
                <Button
                  onClick={() => {
                    setIsEditingDetails(false);
                    setDetails({
                      marks10th: userData.marks10th,
                      marks12th: userData.marks12th,
                      cgpa: userData.cgpa,
                      linkedinProfile: userData.linkedinProfile,
                      githubLink: userData.githubLink,
                    });
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">10th Grade Marks</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {userData.marks10th || 'Not provided'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">12th Grade Marks</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {userData.marks12th || 'Not provided'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">CGPA</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {userData.cgpa || 'Not provided'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">LinkedIn Profile</p>
                {userData.linkedinProfile ? (
                  <a
                    href={userData.linkedinProfile}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    View Profile
                  </a>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">Not provided</p>
                )}
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">GitHub Profile</p>
                {userData.githubLink ? (
                  <a
                    href={userData.githubLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    View Profile
                  </a>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">Not provided</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <button
            onClick={() => navigate('/dashboard/job-seeker/job-roles')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700 text-left group"
          >
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg w-fit mb-4 group-hover:scale-110 transition-transform">
              <Briefcase className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Job Roles</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Discover roles matching your skills
            </p>
          </button>

          <button
            onClick={() => navigate('/dashboard/job-seeker/github-analysis')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700 text-left group"
          >
            <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-lg w-fit mb-4 group-hover:scale-110 transition-transform">
              <Award className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">GitHub Profile Analysis</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Public repositories & detected skills
            </p>
          </button>

          <button
            onClick={() => navigate('/dashboard/job-seeker/recommendations')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700 text-left group"
          >
            <div className="p-3 bg-yellow-100 dark:bg-yellow-900 rounded-lg w-fit mb-4 group-hover:scale-110 transition-transform">
              <Lightbulb className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Recommendations</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Skills to enhance your career
            </p>
          </button>

          <button
            onClick={() => navigate('/dashboard/job-seeker/skill-analysis')}
            className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-200 dark:border-gray-700 text-left group relative overflow-hidden"
          >
            <div className="absolute top-2 right-2 px-2 py-0.5 bg-green-500 text-white text-xs font-bold rounded">NEW</div>
            <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg w-fit mb-4 group-hover:scale-110 transition-transform">
              <Target className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Skill Analysis</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              Job readiness & skill gaps
            </p>
          </button>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/job-roles" element={<JobRolesPage />} />
      <Route path="/github-analysis" element={<ResumeEnhancementPage />} />
      <Route path="/resume-enhancement" element={<ResumeEnhancementPage />} />
      <Route path="/recommendations" element={<JobRecommendationsPage />} />
      <Route path="/skill-analysis" element={<SkillAnalysisPage />} />
    </Routes>
  );
}

// Sub-pages
function JobRolesPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const [jobs, setJobs] = useState<SearchedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{
    total: number;
    matched: number;
    avgScore: number;
    companies: number;
    sources: string[];
    skillsUsed: string[];
    location: string | null;
    isDemoFallback: boolean;
  } | null>(null);
  const [searchSkill, setSearchSkill] = useState('');
  const [locationFilter, setLocationFilter] = useState('India');
  const [jobTypeFilter, setJobTypeFilter] = useState<string>('All');
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [jobMatches, setJobMatches] = useState<JobMatch[] | null>(null);

  // Get all user skills
  const allSkills = [...userData.profile.skills, ...userData.jobSeekerSkills];

  // Parse user's academic details for eligibility check
  const userCgpa = parseFloat(userData.cgpa) || 0;
  const user10th = parseFloat(userData.marks10th?.replace('%', '')) || 0;
  const user12th = parseFloat(userData.marks12th?.replace('%', '')) || 0;

  // Check if user meets job criteria
  const checkEligibility = (job: SearchedJob) => {
    if (!job.criteria) return { eligible: true, reason: '' };
    
    const { min_cgpa, min_10th, min_12th } = job.criteria;
    const reasons: string[] = [];
    
    if (min_cgpa && userCgpa < min_cgpa) {
      reasons.push(`CGPA ${min_cgpa}+ required`);
    }
    if (min_10th && user10th < min_10th) {
      reasons.push(`10th ${min_10th}%+ required`);
    }
    if (min_12th && user12th < min_12th) {
      reasons.push(`12th ${min_12th}%+ required`);
    }
    
    return {
      eligible: reasons.length === 0,
      reason: reasons.join(', ')
    };
  };

  const fetchJobs = async (additionalSkills: string[] = [], location?: string) => {
    setLoading(true);
    setError(null);
    try {
      const skillsToSearch = [...allSkills, ...additionalSkills].filter(Boolean);
      
      const data = await searchJobs({
        skills: skillsToSearch,
        syllabus_data_url: userData.syllabus?.content || null,
        location: location || locationFilter || null,
        limit: 30,
      });
      setJobs(data.jobs || []);
      setJobMatches(null);
      setMatchError(null);
      setStats({
        total: data.total_found,
        matched: data.jobs_with_skill_match,
        avgScore: data.average_match_score,
        companies: data.unique_companies,
        sources: data.sources,
        skillsUsed: data.skills_searched,
        location: data.location_filter,
        isDemoFallback: data.is_demo_fallback,
      });
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs([], locationFilter);
  }, []);

  const handleSearch = () => {
    fetchJobs(searchSkill.trim() ? [searchSkill.trim()] : [], locationFilter);
  };

  const runJobMatching = async () => {
    if (jobs.length === 0) return;
    setMatching(true);
    setMatchError(null);
    try {
      const twin = await createStudentSkillTwin(makeSelfDeclaredEvidence(allSkills));
      const studentRecords: StudentEvidenceInput[] = twin.flatMap((record) => record.evidence.map((item) => ({
        skill: record.skill,
        source: item.source,
        evidence: item.evidence,
        proficiency: item.proficiency as StudentEvidenceInput['proficiency'],
        confidence: item.confidence as StudentEvidenceInput['confidence'],
      })));
      const jobInputs = await Promise.all(jobs.map(async (job, index) => {
        const skills = job.skills ?? (await extractSkills([job.title, job.description || '', ...(job.tags || [])].join('\n'))).extracted_skills;
        return {
          job_id: job.job_id || job.url || `${job.title}|${job.company}|${index}`,
          title: job.title,
          career_role: job.career_role,
          company: job.company,
          skills,
        };
      }));
      const response = await matchJobs(studentRecords, jobInputs);
      setJobMatches(response.matches);
    } catch (err) {
      setMatchError(apiErrorMessage(err));
    } finally {
      setMatching(false);
    }
  };

  const getMatchColor = (score: number) => {
    if (score >= 50) return 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300';
    if (score >= 25) return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300';
    return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
  };

  return (
    <div className="max-w-6xl mx-auto">
      <Button
        onClick={() => navigate('/dashboard/job-seeker')}
        variant="ghost"
        className="mb-6 hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Job Seeker Dashboard
      </Button>

      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">🔍 Job Roles & Companies</h1>
        <p className="text-gray-600 dark:text-gray-300">
          Real-time jobs from Remotive, Arbeitnow & more — matched to your skills
        </p>
      </div>

      {/* Search & Refresh */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 mb-6 border border-gray-200 dark:border-gray-700">
        <div className="flex flex-col gap-3">
          <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex min-w-0 flex-1 gap-2">
              <Input
                value={searchSkill}
                onChange={(e) => setSearchSkill(e.target.value)}
                placeholder="Add a skill to search (e.g., Python, React)"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="bg-gray-50 dark:bg-gray-700"
              />
            </div>
            <div className="flex gap-2">
              <div className="relative">
                <MapPin className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <Input
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                  placeholder="Location (e.g., India, Bangalore)"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full bg-gray-50 pl-10 dark:bg-gray-700 sm:w-48"
                />
              </div>
              <Button onClick={handleSearch} className="bg-blue-600 hover:bg-blue-700">
                <Search className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs text-gray-500 dark:text-gray-400">📍 Location:</span>
              {['India', 'Bangalore', 'Remote', 'Mumbai', 'Hyderabad', 'Delhi'].map((loc) => (
                <button
                  key={loc}
                  onClick={() => { setLocationFilter(loc); fetchJobs([], loc); }}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    locationFilter === loc 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-blue-100 dark:hover:bg-blue-900'
                  }`}
                >
                  {loc}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs text-gray-500 dark:text-gray-400">💼 Job Type:</span>
              {['All', 'Full-time', 'Part-time', 'Remote', 'Hybrid'].map((type) => (
                <button
                  key={type}
                  onClick={() => setJobTypeFilter(type)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    jobTypeFilter === type 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-green-100 dark:hover:bg-green-900'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
          <Button onClick={() => fetchJobs([], locationFilter)} variant="outline" disabled={loading} className="self-end">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh Jobs
          </Button>
        </div>
        
        {/* Skills being searched */}
        {stats?.skillsUsed?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Searching for:</span>
            {stats.skillsUsed.slice(0, 10).map((skill: string, i: number) => (
              <span key={i} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-xs">
                {skill}
              </span>
            ))}
            {stats.skillsUsed.length > 10 && (
              <span className="text-xs text-gray-500">+{stats.skillsUsed.length - 10} more</span>
            )}
          </div>
        )}
      </div>

      {/* Stats */}
      {stats && !loading && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 text-center">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Jobs Found</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 text-center">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.matched}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Skill Matches</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 text-center">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {stats.avgScore < 100 ? `${stats.avgScore}%` : '—'}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Avg Match Score</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 text-center">
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">{stats.companies}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Companies</div>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
          <p className="text-gray-600 dark:text-gray-300">Fetching live job listings...</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Searching Remotive, Arbeitnow, and more...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl p-6 text-center">
          <p className="text-red-600 dark:text-red-400 font-medium">{error}</p>
          <Button onClick={() => fetchJobs()} className="mt-4 bg-red-600 hover:bg-red-700">
            Try Again
          </Button>
        </div>
      )}

      {!loading && !error && stats?.isDemoFallback && jobs.length > 0 && (
        <div role="status" className="mb-5 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-200">
          Demo job data — synthetic records for skill matching only; these are not real job openings.
        </div>
      )}

      {!loading && !error && jobs.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-5 mb-6 border border-gray-200 dark:border-gray-700">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">CareerAlign job skill matching</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Compares your supplied skills with canonical skills extracted from these listings; this is not a hiring probability.</p>
            </div>
            <Button onClick={runJobMatching} disabled={matching}>
              {matching ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Target className="w-4 h-4 mr-2" />}
              {matching ? 'Matching jobs...' : 'Match listed jobs'}
            </Button>
          </div>
          {matchError && <p role="alert" className="text-sm text-red-600 mt-3">{matchError}</p>}
          {jobMatches && (jobMatches.length === 0 ? (
            <p className="text-sm text-gray-500 mt-4">No job matches were returned.</p>
          ) : (
            <div className="grid md:grid-cols-2 gap-3 mt-4">
              {jobMatches.map((match) => (
                <div key={match.job_id} className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{match.title}</h3>
                      {match.company && <p className="text-sm text-gray-600 dark:text-gray-400">{match.company}</p>}
                      {match.career_role && <p className="text-xs text-gray-500 dark:text-gray-400">{match.career_role}</p>}
                    </div>
                    <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">{match.score}% alignment</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{match.explanation}</p>
                  <div className="flex flex-wrap gap-1 mt-3">
                    {match.matched_skills.map((skill) => <SkillChip key={`matched-${skill}`} tone="green">Matched: {skill}</SkillChip>)}
                    {match.partial_skills.map((skill) => <SkillChip key={`partial-${skill}`} tone="amber">Partial: {skill}</SkillChip>)}
                    {match.missing_skills.map((skill) => <SkillChip key={`missing-${skill}`} tone="slate">Missing: {skill}</SkillChip>)}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Jobs List */}
      {!loading && !error && (
        <div className="space-y-4">
          {jobs.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-8 text-center border border-gray-200 dark:border-gray-700">
              <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-300 font-medium">No jobs found matching your skills</p>
              <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">Try adding more skills or broadening your search</p>
            </div>
          ) : (
            jobs
              .filter((job) => jobTypeFilter === 'All' || job.job_type?.toLowerCase().includes(jobTypeFilter.toLowerCase()))
              .map((job, index) => {
                const eligibility = checkEligibility(job);
                return (
                  <div
                    key={index}
                    className={`bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border transition-all duration-200 ${
                      eligibility.eligible 
                        ? 'border-gray-200 dark:border-gray-700 hover:shadow-lg' 
                        : 'border-red-200 dark:border-red-800 opacity-75'
                    }`}
                  >
                    <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-start gap-3 mb-3">
                          <div className="flex-1">
                            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{job.title}</h3>
                            <p className="text-gray-600 dark:text-gray-300 font-medium">{job.company}</p>
                            {job.career_role && <p className="text-sm text-gray-500 dark:text-gray-400">{job.career_role}</p>}
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            {job.match_score > 0 && job.match_score < 100 && (
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getMatchColor(job.match_score)}`}>
                                {job.match_score}% match
                              </span>
                            )}
                            {!eligibility.eligible && (
                              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300">
                                Not Applicable
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-4 text-sm mb-3">
                          <span className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                            <MapPin className="w-4 h-4" />
                            {job.location || 'Remote'}
                          </span>
                          {job.days_ago !== undefined && <span className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                            <Clock className="w-4 h-4" />
                            {job.days_ago === 0 ? 'Today' : `${job.days_ago} days ago`}
                          </span>}
                          <span className="flex items-center gap-1 text-gray-500 dark:text-gray-500">
                            <TrendingUp className="w-4 h-4" />
                            {job.source}
                          </span>
                          {job.job_type && (
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              job.job_type === 'Remote' ? 'bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300' :
                              job.job_type === 'Hybrid' ? 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300' :
                              job.job_type === 'Part-time' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300' :
                              'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                            }`}>
                              {job.job_type}
                            </span>
                          )}
                        </div>

                        {/* Company Criteria */}
                        {job.criteria && (
                          <div className="mb-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">📋 Eligibility Criteria:</p>
                            <div className="flex flex-wrap gap-2 text-xs">
                              <span className={`px-2 py-0.5 rounded ${
                                userCgpa >= job.criteria.min_cgpa 
                                  ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' 
                                  : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                              }`}>
                                CGPA: {job.criteria.min_cgpa}+ {userCgpa >= job.criteria.min_cgpa ? '✓' : '✗'}
                              </span>
                              <span className={`px-2 py-0.5 rounded ${
                                user10th >= job.criteria.min_10th 
                                  ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' 
                                  : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                              }`}>
                                10th: {job.criteria.min_10th}%+ {user10th >= job.criteria.min_10th ? '✓' : '✗'}
                              </span>
                              <span className={`px-2 py-0.5 rounded ${
                                user12th >= job.criteria.min_12th 
                                  ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300' 
                                  : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                              }`}>
                                12th: {job.criteria.min_12th}%+ {user12th >= job.criteria.min_12th ? '✓' : '✗'}
                              </span>
                            </div>
                            {!eligibility.eligible && (
                              <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                                ⚠️ You don't meet: {eligibility.reason}
                              </p>
                            )}
                          </div>
                        )}

                        {/* Matched Skills */}
                        {job.matched_skills?.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Your matching skills:</p>
                            <div className="flex flex-wrap gap-1">
                              {job.matched_skills.map((skill: string, i: number) => (
                                <span key={i} className="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded text-xs font-medium">
                                  ✓ {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Tags */}
                        {job.tags?.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {job.tags.slice(0, 5).map((tag: string, i: number) => (
                              <span key={i} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {job.url ? <div className="flex lg:flex-col gap-2 lg:min-w-[140px]">
                        <a href={job.url} target="_blank" rel="noopener noreferrer" className="flex-1 lg:flex-none">
                          <Button className={`w-full ${eligibility.eligible ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-gray-400 hover:bg-gray-500 text-white cursor-not-allowed'}`} disabled={!eligibility.eligible}>
                            <ExternalLink className="w-4 h-4 mr-2" />
                            {eligibility.eligible ? 'Apply' : 'Not Eligible'}
                          </Button>
                        </a>
                      </div> : <span className="self-center text-xs text-amber-700 dark:text-amber-300">Demo only — not a live vacancy</span>}
                    </div>
                  </div>
                );
              })
          )}

          {/* Sources Attribution */}
          {jobs.length > 0 && stats?.sources && (
            <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">
              Jobs sourced from: {stats.sources.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResumeEnhancementPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState<Awaited<ReturnType<typeof analyzeGitHubProfile>> | null>(null);
  const [githubUsername, setGithubUsername] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const match = userData.githubLink.match(/github\.com\/([^\/]+)/);
    setGithubUsername(match?.[1] || userData.githubLink || '');
  }, [userData.githubLink]);

  const fetchGitHubData = async () => {
    if (!githubUsername.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setAnalysisData(await analyzeGitHubProfile(githubUsername.trim()));
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <Button onClick={() => navigate('/dashboard/job-seeker')} variant="ghost" className="mb-6">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Job Seeker Dashboard
      </Button>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">GitHub Profile Analysis</h1>
        <p className="text-gray-600 dark:text-gray-300">Review public GitHub repositories and detected skills. Resume feedback is available separately on the Resume page.</p>
      </div>
      <div className="bg-slate-800 rounded-xl shadow-lg p-6 mb-6 border border-slate-700">
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1">
            <Label className="text-white mb-2 block font-semibold">GitHub Username or Profile URL</Label>
            <Input value={githubUsername} onChange={(event) => setGithubUsername(event.target.value)} placeholder="Enter your GitHub username" className="bg-white text-gray-900" />
          </div>
          <Button onClick={fetchGitHubData} disabled={loading || !githubUsername.trim()} className="bg-purple-600 hover:bg-purple-700 text-white">
            {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Github className="w-4 h-4 mr-2" />}
            {loading ? 'Loading projects...' : 'Load GitHub projects'}
          </Button>
        </div>
      </div>
      {error && <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700">{error}</div>}
      {!loading && analysisData && (
        <div className="space-y-6">
          <section className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Projects ({analysisData.projects.length})</h2>
            {analysisData.projects.length === 0 ? <p className="text-slate-300">No public projects were returned.</p> : (
              <div className="grid md:grid-cols-2 gap-3">
                {analysisData.projects.map((project) => (
                  <a key={project.url || project.name} href={project.url} target="_blank" rel="noopener noreferrer" className="block bg-white rounded-lg p-4 border border-slate-200">
                    <span className="font-semibold text-slate-900">{project.name}</span>
                    <ExternalLink className="w-4 h-4 inline ml-2 text-slate-400" />
                    {project.description && <p className="text-sm text-slate-600 mt-2">{project.description}</p>}
                    <p className="text-xs text-slate-500 mt-2">{project.stars} stars</p>
                  </a>
                ))}
              </div>
            )}
          </section>
          <section className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-xl font-bold text-white mb-4">Skills found in public GitHub profile data</h2>
            {analysisData.skills.length === 0 ? <p className="text-slate-300">No taxonomy skills were detected in the returned profile data.</p> : (
              <div className="flex flex-wrap gap-2">{analysisData.skills.map((skill) => <span key={skill} className="px-3 py-1 bg-purple-600 text-white rounded-full text-sm">{skill}</span>)}</div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function JobRecommendationsPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const [predictingRole, setPredictingRole] = useState(false);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [rolePredictions, setRolePredictions] = useState<RolePrediction[] | null>(null);

  const predictionInput = (() => {
    const resumeSkills = userData.resume?.extractedSkills ?? [];
    const declaredSkills = [...userData.profile.skills, ...userData.studentSkills, ...userData.jobSeekerSkills];
    const parts = [
      userData.jobSeekerResume.trim(),
      userData.studentResume.trim(),
      resumeSkills.length ? `Resume-derived skills: ${resumeSkills.join(', ')}` : '',
      declaredSkills.length ? `User-provided skills: ${declaredSkills.join(', ')}` : '',
    ].filter(Boolean);
    return parts.join('\n');
  })();

  const requestRoleRecommendation = async () => {
    if (!predictionInput.trim()) {
      setPredictionError('Add skills to your profile or process a resume before requesting an AI career recommendation.');
      setRolePredictions(null);
      return;
    }
    setPredictingRole(true);
    setPredictionError(null);
    setRolePredictions(null);
    try {
      const results = await predictRole(predictionInput);
      if (!results.length) {
        setPredictionError('The classifier did not return a role. Try adding more resume or skill information.');
      } else {
        setRolePredictions(results);
      }
    } catch (error) {
      setPredictionError(apiErrorMessage(error));
    } finally {
      setPredictingRole(false);
    }
  };

  const recommendations = [
    {
      title: 'Learn Cloud Computing',
      description: 'Master AWS, Azure, or Google Cloud to become a Cloud Solutions Architect',
      skills: ['AWS', 'Azure', 'Google Cloud', 'Terraform'],
      potentialRole: 'Cloud Solutions Architect',
      salary: '$140k - $200k',
      demand: 'Very High',
      color: 'blue',
      courseUrl: 'https://www.coursera.org/professional-certificates/aws-cloud-solutions-architect',
    },
    {
      title: 'Master Machine Learning',
      description: 'Dive into AI/ML to transition into high-demand data science roles',
      skills: ['Python', 'TensorFlow', 'PyTorch', 'Statistics'],
      potentialRole: 'Machine Learning Engineer',
      salary: '$150k - $220k',
      demand: 'Extremely High',
      color: 'purple',
      courseUrl: 'https://www.coursera.org/specializations/machine-learning-introduction',
    },
    {
      title: 'Specialize in Cybersecurity',
      description: 'Become a security expert with certifications like CISSP or CEH',
      skills: ['Network Security', 'Penetration Testing', 'SIEM', 'Cryptography'],
      potentialRole: 'Security Engineer',
      salary: '$130k - $190k',
      demand: 'Very High',
      color: 'red',
      courseUrl: 'https://www.coursera.org/professional-certificates/google-cybersecurity',
    },
    {
      title: 'Master Mobile Development',
      description: 'Build cross-platform apps and become a Mobile Development Expert',
      skills: ['React Native', 'Flutter', 'iOS', 'Android'],
      potentialRole: 'Senior Mobile Developer',
      salary: '$120k - $180k',
      demand: 'High',
      color: 'green',
      courseUrl: 'https://www.udemy.com/course/the-complete-react-native-and-redux-course/',
    },
    {
      title: 'Learn Blockchain Technology',
      description: 'Enter the Web3 space with blockchain and smart contract development',
      skills: ['Solidity', 'Ethereum', 'Smart Contracts', 'Web3.js'],
      potentialRole: 'Blockchain Developer',
      salary: '$140k - $210k',
      demand: 'High',
      color: 'orange',
      courseUrl: 'https://www.coursera.org/specializations/blockchain',
    },
    {
      title: 'Enhance with System Design',
      description: 'Master system design to qualify for senior and principal engineering roles',
      skills: ['Distributed Systems', 'Microservices', 'Scalability', 'Architecture'],
      potentialRole: 'Principal Engineer',
      salary: '$180k - $300k',
      demand: 'Very High',
      color: 'indigo',
      courseUrl: 'https://www.educative.io/courses/grokking-modern-system-design-interview-for-engineers-managers',
    },
  ];

  const handleStartLearning = (courseUrl: string) => {
    window.open(courseUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="max-w-6xl mx-auto">
      <Button
        onClick={() => navigate('/dashboard/job-seeker')}
        variant="ghost"
        className="mb-6 hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Job Seeker Dashboard
      </Button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Career Recommendations</h1>
        <p className="text-gray-600 dark:text-gray-300">
          Get a role classification from your existing resume and profile skills.
        </p>
      </div>

      <section className="bg-slate-800 rounded-xl shadow-lg p-6 mb-8 border border-slate-700" aria-labelledby="ai-career-heading">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 id="ai-career-heading" className="text-xl font-bold text-white">AI career recommendation</h2>
            <p className="text-sm text-slate-300 mt-1">Uses resume-derived and user-entered skills saved in your profile. This is an ML classification result, not a guarantee of suitability.</p>
            <p className="text-xs text-slate-400 mt-2">{predictionInput.trim() ? `Input available: ${predictionInput.length} characters from your current profile information.` : 'No resume-derived or profile skills are available yet.'}</p>
          </div>
          <Button onClick={requestRoleRecommendation} disabled={predictingRole} className="bg-purple-600 hover:bg-purple-700 text-white shrink-0">
            {predictingRole ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Lightbulb className="w-4 h-4 mr-2" />}
            {predictingRole ? 'Getting recommendation...' : 'Get AI Career Recommendation'}
          </Button>
        </div>
        {predictionError && <p role="alert" className="mt-4 rounded-lg bg-red-100 text-red-800 px-4 py-3 text-sm">{predictionError}</p>}
        {rolePredictions && (
          <div className="mt-5 rounded-lg bg-white p-4" aria-live="polite">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-wide text-slate-500">Top AI role recommendation</p>
                <h3 className="break-words text-2xl font-bold text-slate-900">{rolePredictions[0].role}</h3>
              </div>
              <p className="text-sm text-slate-600">Model score: {rolePredictions[0].confidence}% <span className="block text-xs">Not a calibrated measure of career fit.</span></p>
            </div>
            {rolePredictions.length > 1 && <div className="mt-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-800">Other returned roles</h4>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
                {rolePredictions.slice(1).map((item) => <div key={item.role} className="flex min-w-0 items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                  <span className="break-words text-sm font-medium text-slate-800">{item.role}</span>
                  <span className="shrink-0 text-xs text-slate-600">{item.confidence}%</span>
                </div>)}
              </div>
            </div>}
            <p className="mt-3 text-xs text-slate-500">This prediction does not change your selected target role. Choose a target role separately when using Skill Analysis or Generate Roadmap.</p>
          </div>
        )}
      </section>

      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">General career exploration ideas</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">These static learning examples are not personalized or generated from your profile.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">{rec.title}</h3>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                rec.demand === 'Extremely High' ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300' :
                rec.demand === 'Very High' ? 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300' :
                'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300'
              }`}>
                {rec.demand} Demand
              </span>
            </div>
            <p className="text-gray-600 dark:text-gray-300 text-sm mb-4">{rec.description}</p>
            <div className="mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Skills to Learn:</p>
              <div className="flex flex-wrap gap-2">
                {rec.skills.map((skill, skillIndex) => (
                  <span
                    key={skillIndex}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-xs font-medium"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-4 mb-4">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Potential Role:</p>
              <p className="font-semibold text-gray-900 dark:text-white mb-2">{rec.potentialRole}</p>
              <p className="text-sm text-gray-700 dark:text-gray-300">💰 {rec.salary}</p>
            </div>
            <Button
              onClick={() => handleStartLearning(rec.courseUrl)}
              className={`w-full text-white shadow-md ${
              rec.color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' :
              rec.color === 'purple' ? 'bg-purple-600 hover:bg-purple-700' :
              rec.color === 'red' ? 'bg-red-600 hover:bg-red-700' :
              rec.color === 'green' ? 'bg-green-600 hover:bg-green-700' :
              rec.color === 'orange' ? 'bg-orange-600 hover:bg-orange-700' :
              'bg-indigo-600 hover:bg-indigo-700'
            }`}>
              Start Learning ↗
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

// Skill Analysis / Job Readiness Page
function SkillAnalysisPage() {
  const navigate = useNavigate();
  const { userData } = useUser();
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState<{
    gaps: SkillGapResponse;
    alignment: CareerAlignmentResponse;
    studentSkills: string[];
    githubSkills: string[];
    syllabusSkills: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [roleError, setRoleError] = useState<string | null>(null);
  const [githubUsername, setGithubUsername] = useState('');
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('');
  const userInputSkills = [...new Set([...userData.profile.skills, ...userData.jobSeekerSkills])];

  useEffect(() => {
    const match = userData.githubLink.match(/github\.com\/([^\/]+)/);
    setGithubUsername(match?.[1] || userData.githubLink || '');
  }, [userData.githubLink]);

  useEffect(() => {
    let active = true;
    listCareerRoles().then((roles) => {
      if (active) setAvailableRoles(roles);
    }).catch((err: unknown) => {
      if (active) setRoleError(apiErrorMessage(err));
    });
    return () => { active = false; };
  }, []);

  const analyzeSkills = async () => {
    if (!selectedRole) {
      setError('Select a target career role before analyzing.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const records: StudentEvidenceInput[] = makeSelfDeclaredEvidence(userInputSkills);
      records.push(...(userData.resume?.skillEvidence ?? []));
      let githubSkills: string[] = [];
      if (githubUsername.trim()) {
        const username = githubUsername.trim().match(/github\.com\/([^\/]+)/)?.[1] || githubUsername.trim();
        const github = await analyzeGitHubProfile(username);
        githubSkills = github.skills;
        records.push(...github.skills.map((skill) => ({
          skill,
          source: 'github' as const,
          evidence: 'Skill listed by GitHub profile analysis: ' + skill,
          confidence: 'low' as const,
        })));
      }

      const syllabusText = userData.studentSyllabus.join('\n');
      let syllabusSkills: string[] = [];
      if (syllabusText.trim()) {
        syllabusSkills = (await extractSkills(syllabusText)).extracted_skills;
        records.push(...syllabusSkills.map((skill) => ({
          skill,
          source: 'syllabus' as const,
          evidence: 'Skill mention in supplied syllabus topics: ' + skill,
          confidence: 'low' as const,
        })));
      }

      const twin = await createStudentSkillTwin(records);
      const evidenceRecords: StudentEvidenceInput[] = twin.flatMap((record) => record.evidence.map((item) => ({
        skill: record.skill,
        source: item.source,
        evidence: item.evidence,
        proficiency: item.proficiency as StudentEvidenceInput['proficiency'],
        confidence: item.confidence as StudentEvidenceInput['confidence'],
      })));
      const [gaps, alignment] = await Promise.all([
        analyzeSkillGap(evidenceRecords, selectedRole),
        getCareerAlignment(evidenceRecords, selectedRole),
      ]);
      setAnalysisData({
        gaps,
        alignment,
        studentSkills: twin.map((item) => item.skill),
        githubSkills,
        syllabusSkills,
      });
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const readinessScore = analysisData?.alignment.career_readiness.career_readiness_score ?? null;
  const skillGroups = analysisData ? [
    { title: 'Matched skills', items: analysisData.gaps.matched_skills },
    { title: 'Partial skills', items: analysisData.gaps.partial_skills },
    { title: 'Missing skills', items: analysisData.gaps.missing_skills },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto">
      <Button onClick={() => navigate('/dashboard/job-seeker')} variant="ghost" className="mb-6"><ArrowLeft className="w-4 h-4 mr-2" /> Back to Job Seeker Dashboard</Button>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Skill Gap Analysis</h1>
        <p className="text-gray-600 dark:text-gray-300">The backend compares supplied skill evidence with the selected CareerAlign role.</p>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 mb-6 border border-slate-700">
        <h2 className="text-lg font-bold text-white mb-3">Available evidence</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="bg-white rounded-lg p-3 text-center"><div className="text-2xl font-bold text-slate-800">{userInputSkills.length}</div><div className="text-xs text-slate-600">Declared skills</div></div>
          <div className="bg-white rounded-lg p-3 text-center"><div className="text-2xl font-bold text-slate-800">{analysisData?.githubSkills.length || 0}</div><div className="text-xs text-slate-600">GitHub skills</div></div>
          <div className="bg-white rounded-lg p-3 text-center"><div className="text-2xl font-bold text-slate-800">{analysisData?.syllabusSkills.length || 0}</div><div className="text-xs text-slate-600">Extracted from entered syllabus topics</div></div>
        </div>
        <p className="text-xs text-slate-300 mt-3">Resume-derived evidence is included alongside listed skills. LinkedIn and uploaded syllabus files are not parsed here.</p>
      </div>

      <div className="bg-slate-800 rounded-xl p-5 mb-6 border border-slate-700">
        <Label className="text-white mb-3 block font-semibold text-lg">Select target career role</Label>
        {availableRoles.length === 0 && !roleError && <p className="text-slate-300">Loading roles...</p>}
        {roleError && <p role="alert" className="text-red-300">{roleError}</p>}
        <div className="flex flex-wrap gap-2">{availableRoles.map((role) => <Button key={role} onClick={() => setSelectedRole(role)} variant={selectedRole === role ? 'default' : 'outline'} className={selectedRole === role ? 'bg-purple-600 text-white' : 'bg-white text-slate-800'}>{role}</Button>)}</div>
        {selectedRole && <p className="mt-3 text-sm text-slate-200">Selected: <strong>{selectedRole}</strong></p>}
      </div>

      <div className="bg-slate-800 rounded-xl p-5 mb-6 border border-slate-700">
        <div className="flex flex-col sm:flex-row gap-3 items-end">
          <div className="flex-1 w-full"><Label className="text-white mb-2 block">GitHub username or URL (optional)</Label><Input value={githubUsername} onChange={(event) => setGithubUsername(event.target.value)} placeholder="Enter GitHub username" className="bg-white text-gray-900" /></div>
          <Button onClick={analyzeSkills} disabled={loading || !selectedRole} className="bg-green-600 hover:bg-green-700 text-white">{loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Target className="w-4 h-4 mr-2" />}{loading ? 'Analyzing...' : 'Analyze skills'}</Button>
        </div>
      </div>

      {error && <div role="alert" className="bg-red-50 border border-red-200 rounded-xl p-5 mb-6"><p className="text-red-700">{error}</p><Button onClick={analyzeSkills} disabled={loading || !selectedRole} className="mt-3">Try Again</Button></div>}
      {loading && <div className="flex items-center justify-center gap-3 py-10"><Loader2 className="w-8 h-8 text-purple-600 animate-spin" /><p>Analyzing skill evidence...</p></div>}

      {analysisData && !loading && (
        <div className="space-y-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 text-center"><h2 className="text-lg font-bold text-white">Career Alignment Score</h2><p className="text-5xl font-bold text-white my-3">{readinessScore === null ? '—' : readinessScore + '%'}</p><p className="text-sm text-slate-300">{analysisData.alignment.career_readiness.interpretation}</p><p className="text-xs text-slate-400 mt-2">This is skill alignment, not hiring or placement probability.</p></div>
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700"><h2 className="text-lg font-bold text-white mb-3">{selectedRole} skill counts</h2><div className="grid grid-cols-3 gap-2 text-center"><div className="bg-green-100 rounded p-3"><strong>{analysisData.gaps.matched_count}</strong><p className="text-xs">Matched</p></div><div className="bg-yellow-100 rounded p-3"><strong>{analysisData.gaps.partial_count}</strong><p className="text-xs">Partial</p></div><div className="bg-slate-100 rounded p-3"><strong>{analysisData.gaps.missing_count}</strong><p className="text-xs">Missing</p></div></div></div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">{skillGroups.map((group) => <section key={group.title} className="min-w-0 rounded-xl border border-slate-700 bg-slate-800 p-5"><h2 className="mb-3 font-bold text-white">{group.title} ({group.items.length})</h2>{group.items.length === 0 ? <p className="text-sm text-slate-400">No skills in this group.</p> : <div className="flex flex-wrap gap-2">{group.items.map((item) => <SkillChip key={item.skill} tone={group.title.toLowerCase().includes('missing') ? 'slate' : group.title.toLowerCase().includes('partial') ? 'amber' : 'green'}>{item.skill}</SkillChip>)}</div>}</section>)}</div>

          <section className="bg-slate-800 rounded-xl p-5 border border-slate-700"><h2 className="font-bold text-white mb-3">Prioritized skill gaps</h2>{analysisData.alignment.prioritized_gaps.length === 0 ? <p className="text-sm text-slate-300">No partial or missing role skills were returned.</p> : <div className="space-y-3">{analysisData.alignment.prioritized_gaps.map((gap) => <div key={gap.skill} className="bg-white rounded-lg p-3"><div className="flex justify-between gap-2"><strong className="text-slate-900">{gap.skill}</strong><span className="text-xs text-slate-600">{gap.gap_type} · {gap.industry_priority}</span></div><p className="text-sm text-slate-600 mt-1">{gap.reason}</p></div>)}</div>}</section>
          <section className="rounded-xl border border-slate-700 bg-slate-800 p-5"><h2 className="mb-3 font-bold text-white">Student Skill Twin evidence</h2>{analysisData.studentSkills.length === 0 ? <p className="text-sm text-slate-300">No recognized skill evidence was supplied.</p> : <div className="flex flex-wrap gap-2">{analysisData.studentSkills.map((skill) => <SkillChip key={skill} tone="purple">{skill}</SkillChip>)}</div>}</section>
          <Button onClick={() => navigate('/dashboard/job-seeker/job-roles')}><Search className="w-4 h-4 mr-2" />Search and match jobs</Button>
        </div>
      )}
    </div>
  );
}
