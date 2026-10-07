import { createContext, useContext, useState, ReactNode } from 'react';

interface UserProfile {
  name: string;
  email: string;
  hobbies: string[];
  skills: string[];
  profilePicture: string;
}

interface SyllabusFile {
  id: string;
  fileName: string;
  content: string;
  type: 'pdf' | 'image' | 'text';
  uploadedAt: string;
}

interface ResumeSkillEvidence {
  skill: string;
  source: 'resume';
  evidence: string;
  proficiency: 'unknown';
  confidence: 'medium';
}

interface UserData {
  isAuthenticated: boolean;
  userType: 'student' | 'job-seeker' | null;
  profile: UserProfile;
  syllabus: {
    fileName: string;
    content: string;
  } | null;
  syllabusFiles: SyllabusFile[];
  resume: {
    fileName: string;
    content: string;
    extractedSkills?: string[];
    skillEvidence?: ResumeSkillEvidence[];
  } | null;
  studentSkills: string[];
  studentSyllabus: string[];
  studentResume: string;
  jobSeekerSkills: string[];
  jobSeekerResume: string;
  marks10th: string;
  marks12th: string;
  cgpa: string;
  linkedinProfile: string;
  githubLink: string;
}

interface UserContextType {
  userData: UserData;
  updateProfile: (profile: Partial<UserProfile>) => void;
  login: (email: string, password: string, userType: 'student' | 'job-seeker') => void;
  signup: (email: string, password: string, name: string, userType: 'student' | 'job-seeker') => void;
  loginWithGoogle: (userType: 'student' | 'job-seeker') => void;
  logout: () => void;
  uploadSyllabus: (fileName: string, content: string) => void;
  uploadResume: (fileName: string, content: string, extractedSkills?: string[], skillEvidence?: ResumeSkillEvidence[]) => void;
  addSyllabusFile: (file: Omit<SyllabusFile, 'id' | 'uploadedAt'>) => void;
  removeSyllabusFile: (id: string) => void;
  updateStudentSkills: (skills: string[]) => void;
  removeStudentSkill: (skill: string) => void;
  updateStudentSyllabus: (syllabus: string[]) => void;
  updateStudentResume: (resume: string) => void;
  updateJobSeekerSkills: (skills: string[]) => void;
  updateJobSeekerResume: (resume: string) => void;
  updateJobSeekerDetails: (details: {
    marks10th?: string;
    marks12th?: string;
    linkedinProfile?: string;
    githubLink?: string;
  }) => void;
  updateStudentDetails: (details: {
    marks10th?: string;
    marks12th?: string;
    cgpa?: string;
    githubLink?: string;
  }) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);
const PROFILE_IDENTITY_STORAGE_KEY = 'careeralignProfileIdentity';

type StoredProfileIdentity = { email: string; name: string; userType: 'student' | 'job-seeker' };

const loadProfileIdentity = (): StoredProfileIdentity | null => {
  try {
    const saved = localStorage.getItem(PROFILE_IDENTITY_STORAGE_KEY);
    if (!saved) return null;
    const identity = JSON.parse(saved) as Partial<StoredProfileIdentity>;
    if (typeof identity.email !== 'string' || !identity.email.trim()) return null;
    if (identity.userType !== 'student' && identity.userType !== 'job-seeker') return null;
    return { email: identity.email, name: typeof identity.name === 'string' ? identity.name : '', userType: identity.userType };
  } catch {
    return null;
  }
};

const saveProfileIdentity = (identity: StoredProfileIdentity) => {
  try { localStorage.setItem(PROFILE_IDENTITY_STORAGE_KEY, JSON.stringify(identity)); } catch { /* Identity may be re-entered at sign-in. */ }
};

const loadResumeFromStorage = (): { fileName: string; content: string } | null => {
  try {
    const saved = localStorage.getItem('uploadedResume');
    if (saved) return JSON.parse(saved);
  } catch {}
  return null;
};

const loadSyllabusFromStorage = (): { fileName: string; content: string } | null => {
  try {
    const saved = localStorage.getItem('uploadedSyllabus');
    if (saved) return JSON.parse(saved);
  } catch {}
  return null;
};

const loadSyllabusFilesFromStorage = (): SyllabusFile[] => {
  try {
    const saved = localStorage.getItem('syllabusFiles');
    if (saved) return JSON.parse(saved);
  } catch {}
  return [];
};

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [userData, setUserData] = useState<UserData>(() => {
    const identity = loadProfileIdentity();
    return {
      isAuthenticated: Boolean(identity),
      userType: identity?.userType ?? null,
      profile: {
        name: identity?.name ?? '',
        email: identity?.email ?? '',
        hobbies: [],
        skills: [],
        profilePicture: '',
      },
      syllabus: loadSyllabusFromStorage(),
      syllabusFiles: loadSyllabusFilesFromStorage(),
      resume: loadResumeFromStorage(),
      studentSkills: [],
      studentSyllabus: [],
      studentResume: '',
      jobSeekerSkills: [],
      jobSeekerResume: '',
      marks10th: '',
      marks12th: '',
      cgpa: '',
      linkedinProfile: '',
      githubLink: '',
    };
  });

  const updateProfile = (profile: Partial<UserProfile>) => {
    setUserData((prev) => {
      const nextProfile = { ...prev.profile, ...profile };
      if (prev.userType && nextProfile.email.trim()) {
        saveProfileIdentity({ email: nextProfile.email, name: nextProfile.name, userType: prev.userType });
      }
      return { ...prev, profile: nextProfile };
    });
  };

  const login = (email: string, password: string, userType: 'student' | 'job-seeker') => {
    saveProfileIdentity({ email, name: email.split('@')[0], userType });
    setUserData((prev) => ({
      ...prev,
      isAuthenticated: true,
      userType,
      profile: {
        ...prev.profile,
        email,
        name: email.split('@')[0],
      },
    }));
  };

  const signup = (email: string, password: string, name: string, userType: 'student' | 'job-seeker') => {
    saveProfileIdentity({ email, name, userType });
    setUserData((prev) => ({
      ...prev,
      isAuthenticated: true,
      userType,
      profile: {
        ...prev.profile,
        email,
        name,
      },
    }));
  };

  const loginWithGoogle = (userType: 'student' | 'job-seeker') => {
    saveProfileIdentity({ email: 'user@gmail.com', name: 'Demo User', userType });
    setUserData((prev) => ({
      ...prev,
      isAuthenticated: true,
      userType,
      profile: {
        ...prev.profile,
        email: 'user@gmail.com',
        name: 'Demo User',
      },
    }));
  };

  const logout = () => {
    try {
      localStorage.removeItem(PROFILE_IDENTITY_STORAGE_KEY);
      if (userData.profile.email.trim()) {
        localStorage.removeItem(`careeralign:lastRoadmapRole:${userData.profile.email.trim().toLowerCase()}`);
      }
    } catch { /* Ignore unavailable browser storage. */ }
    setUserData({
      isAuthenticated: false,
      userType: null,
      profile: {
        name: '',
        email: '',
        hobbies: [],
        skills: [],
        profilePicture: '',
      },
      syllabus: null,
      syllabusFiles: [],
      resume: null,
      studentSkills: [],
      studentSyllabus: [],
      studentResume: '',
      jobSeekerSkills: [],
      jobSeekerResume: '',
      marks10th: '',
      marks12th: '',
      cgpa: '',
      linkedinProfile: '',
      githubLink: '',
    });
  };

  const uploadSyllabus = (fileName: string, content: string) => {
    const syllabusData = { fileName, content };
    try {
      localStorage.setItem('uploadedSyllabus', JSON.stringify(syllabusData));
    } catch (e) {
      console.warn('Could not save syllabus to localStorage:', e);
    }
    setUserData((prev) => ({
      ...prev,
      syllabus: syllabusData,
    }));
  };

  const uploadResume = (fileName: string, content: string, extractedSkills: string[] = [], skillEvidence: ResumeSkillEvidence[] = []) => {
    const resumeData = { fileName, content, extractedSkills, skillEvidence };
    try {
      localStorage.setItem('uploadedResume', JSON.stringify(resumeData));
    } catch (e) {
      console.warn('Could not save resume to localStorage:', e);
    }
    setUserData((prev) => ({
      ...prev,
      resume: resumeData,
    }));
  };

  const updateStudentSkills = (skills: string[]) => {
    setUserData((prev) => ({
      ...prev,
      studentSkills: skills,
    }));
  };

  const removeStudentSkill = (skill: string) => {
    setUserData((prev) => ({
      ...prev,
      studentSkills: prev.studentSkills.filter((s) => s !== skill),
      profile: {
        ...prev.profile,
        skills: prev.profile.skills.filter((s) => s !== skill),
      },
    }));
  };

  const addSyllabusFile = (file: Omit<SyllabusFile, 'id' | 'uploadedAt'>) => {
    const newFile: SyllabusFile = {
      ...file,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      uploadedAt: new Date().toISOString(),
    };
    setUserData((prev) => {
      const updated = [...prev.syllabusFiles, newFile];
      try {
        localStorage.setItem('syllabusFiles', JSON.stringify(updated));
      } catch (e) {
        console.warn('Could not save syllabus files to localStorage:', e);
      }
      return { ...prev, syllabusFiles: updated };
    });
  };

  const removeSyllabusFile = (id: string) => {
    setUserData((prev) => {
      const updated = prev.syllabusFiles.filter((f) => f.id !== id);
      try {
        localStorage.setItem('syllabusFiles', JSON.stringify(updated));
      } catch (e) {
        console.warn('Could not save syllabus files to localStorage:', e);
      }
      return { ...prev, syllabusFiles: updated };
    });
  };

  const updateStudentSyllabus = (syllabus: string[]) => {
    setUserData((prev) => ({
      ...prev,
      studentSyllabus: syllabus,
    }));
  };

  const updateStudentResume = (resume: string) => {
    setUserData((prev) => ({
      ...prev,
      studentResume: resume,
    }));
  };

  const updateJobSeekerSkills = (skills: string[]) => {
    setUserData((prev) => ({
      ...prev,
      jobSeekerSkills: skills,
    }));
  };

  const updateJobSeekerResume = (resume: string) => {
    setUserData((prev) => ({
      ...prev,
      jobSeekerResume: resume,
    }));
  };

  const updateJobSeekerDetails = (details: {
    marks10th?: string;
    marks12th?: string;
    cgpa?: string;
    linkedinProfile?: string;
    githubLink?: string;
  }) => {
    setUserData((prev) => ({
      ...prev,
      ...details,
    }));
  };

  const updateStudentDetails = (details: {
    marks10th?: string;
    marks12th?: string;
    cgpa?: string;
    githubLink?: string;
  }) => {
    setUserData((prev) => ({
      ...prev,
      ...details,
    }));
  };

  return (
    <UserContext.Provider
      value={{
        userData,
        updateProfile,
        login,
        signup,
        loginWithGoogle,
        logout,
        uploadSyllabus,
        uploadResume,
        addSyllabusFile,
        removeSyllabusFile,
        updateStudentSkills,
        removeStudentSkill,
        updateStudentSyllabus,
        updateStudentResume,
        updateJobSeekerSkills,
        updateJobSeekerResume,
        updateJobSeekerDetails,
        updateStudentDetails,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
