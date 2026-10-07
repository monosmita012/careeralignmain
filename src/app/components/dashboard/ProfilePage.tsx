import { useState } from 'react';
import { Camera, Edit2, Save, X, Plus } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useUser } from '../../context/UserContext';
import { toast } from 'sonner';

export default function ProfilePage() {
  const { userData, updateProfile } = useUser();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: userData.profile.name,
    email: userData.profile.email,
    hobbies: userData.profile.hobbies.join(', '),
    skills: userData.profile.skills.join(', '),
  });
  const [newHobby, setNewHobby] = useState('');
  const [newSkill, setNewSkill] = useState('');

  const handleSave = () => {
    updateProfile({
      name: formData.name,
      email: formData.email,
      hobbies: formData.hobbies.split(',').map((h) => h.trim()).filter(Boolean),
      skills: formData.skills.split(',').map((s) => s.trim()).filter(Boolean),
    });
    setIsEditing(false);
    toast.success('Profile updated successfully!');
  };

  const handleCancel = () => {
    setFormData({
      name: userData.profile.name,
      email: userData.profile.email,
      hobbies: userData.profile.hobbies.join(', '),
      skills: userData.profile.skills.join(', '),
    });
    setIsEditing(false);
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        updateProfile({ profilePicture: event.target?.result as string });
        toast.success('Profile picture updated!');
      };
      reader.readAsDataURL(file);
    }
  };

  const addHobby = () => {
    if (newHobby.trim()) {
      const updatedHobbies = [...userData.profile.hobbies, newHobby.trim()];
      updateProfile({ hobbies: updatedHobbies });
      setFormData({ ...formData, hobbies: updatedHobbies.join(', ') });
      setNewHobby('');
      toast.success('Hobby added!');
    }
  };

  const addSkill = () => {
    if (newSkill.trim()) {
      const updatedSkills = [...userData.profile.skills, newSkill.trim()];
      updateProfile({ skills: updatedSkills });
      setFormData({ ...formData, skills: updatedSkills.join(', ') });
      setNewSkill('');
      toast.success('Skill added!');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">My Profile</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Manage your personal information and preferences
          </p>
        </div>
        {!isEditing && (
          <Button
            onClick={() => setIsEditing(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white shadow-md"
          >
            <Edit2 className="w-4 h-4 mr-2" />
            Edit Profile
          </Button>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 border border-gray-200 dark:border-gray-700 transition-colors duration-300">
        {/* Profile Picture */}
        <div className="flex flex-col items-center mb-8">
          <div className="relative group">
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center overflow-hidden shadow-lg">
              {userData.profile.profilePicture ? (
                <img
                  src={userData.profile.profilePicture}
                  alt="Profile"
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-white text-4xl font-bold">
                  {userData.profile.name?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              )}
            </div>
            <label className="absolute bottom-0 right-0 p-2 bg-blue-600 rounded-full cursor-pointer shadow-lg hover:bg-blue-700 transition-colors group-hover:scale-110 transform duration-200">
              <Camera className="w-5 h-5 text-white" />
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </label>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
            Click the camera icon to upload a profile picture
          </p>
        </div>

        {/* Profile Information */}
        <div className="space-y-6">
          <div>
            <Label className="text-gray-700 dark:text-gray-300">Full Name</Label>
            {isEditing ? (
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            ) : (
              <p className="mt-2 text-lg text-gray-900 dark:text-white">{userData.profile.name || 'Not set'}</p>
            )}
          </div>

          <div>
            <Label className="text-gray-700 dark:text-gray-300">Email Address</Label>
            {isEditing ? (
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              />
            ) : (
              <p className="mt-2 text-lg text-gray-900 dark:text-white">{userData.profile.email || 'Not set'}</p>
            )}
          </div>

          <div>
            <Label className="text-gray-700 dark:text-gray-300">Hobbies</Label>
            {isEditing ? (
              <div className="mt-2">
                <Input
                  value={formData.hobbies}
                  onChange={(e) => setFormData({ ...formData, hobbies: e.target.value })}
                  placeholder="Separate hobbies with commas"
                  className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                />
              </div>
            ) : (
              <div className="mt-2">
                {userData.profile.hobbies.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {userData.profile.hobbies.map((hobby, index) => (
                      <span
                        key={index}
                        className="px-4 py-2 bg-pink-100 dark:bg-pink-900 text-pink-700 dark:text-pink-300 rounded-full text-sm font-medium"
                      >
                        {hobby}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">No hobbies added</p>
                )}
                <div className="flex gap-2 mt-3">
                  <Input
                    value={newHobby}
                    onChange={(e) => setNewHobby(e.target.value)}
                    placeholder="Add a new hobby"
                    className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                    onKeyPress={(e) => e.key === 'Enter' && addHobby()}
                  />
                  <Button onClick={addHobby} className="bg-pink-600 hover:bg-pink-700">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div>
            <Label className="text-gray-700 dark:text-gray-300">Skills</Label>
            {isEditing ? (
              <div className="mt-2">
                <Input
                  value={formData.skills}
                  onChange={(e) => setFormData({ ...formData, skills: e.target.value })}
                  placeholder="Separate skills with commas"
                  className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                />
              </div>
            ) : (
              <div className="mt-2">
                {userData.profile.skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {userData.profile.skills.map((skill, index) => (
                      <span
                        key={index}
                        className="px-4 py-2 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400">No skills added</p>
                )}
                <div className="flex gap-2 mt-3">
                  <Input
                    value={newSkill}
                    onChange={(e) => setNewSkill(e.target.value)}
                    placeholder="Add a new skill"
                    className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                    onKeyPress={(e) => e.key === 'Enter' && addSkill()}
                  />
                  <Button onClick={addSkill} className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {isEditing && (
          <div className="flex gap-4 mt-8">
            <Button
              onClick={handleSave}
              className="bg-green-600 hover:bg-green-700 text-white shadow-md flex-1"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
            <Button
              onClick={handleCancel}
              variant="outline"
              className="border-2 border-gray-300 dark:border-gray-600 flex-1 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
