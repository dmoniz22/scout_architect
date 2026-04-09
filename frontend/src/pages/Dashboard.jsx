import { Link } from 'react-router-dom';
import { Calendar, Plus, FolderOpen, ArrowRight, Zap } from 'lucide-react';

export default function Dashboard() {
  const features = [
    {
      title: 'Create a Term Plan',
      description: 'Plan your scouting year with customizable term plans and meeting schedules.',
      icon: Calendar,
      link: '/term-planner',
      color: 'bg-blue-500',
    },
    {
      title: 'Plan a Single Meeting',
      description: 'Create and generate a plan for an individual meeting without a full term.',
      icon: Zap,
      link: '/single-meeting',
      color: 'bg-purple-500',
    },
    {
      title: 'View My Plans',
      description: 'Access and manage your existing term plans, generate meetings, and download materials.',
      icon: FolderOpen,
      link: '/my-plans',
      color: 'bg-green-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="text-center py-8">
        <h2 className="text-3xl font-bold text-slate-800 mb-2">
          Welcome to Scout Leader Lesson Architect
        </h2>
        <p className="text-slate-600 max-w-xl mx-auto">
          Create detailed term plans and meeting guides for your Scout group. 
          Plan activities, track badges, and generate downloadable materials.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-4">
        {features.map((feature) => (
          <Link
            key={feature.link}
            to={feature.link}
            className="card hover:shadow-md transition-shadow group"
          >
            <div className="flex items-start gap-4">
              <div className={`${feature.color} text-white p-3 rounded-lg`}>
                <feature.icon size={24} />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-slate-800 flex items-center gap-2 group-hover:text-scout-blue">
                  {feature.title}
                  <ArrowRight size={16} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </h3>
                <p className="text-sm text-slate-600 mt-1">{feature.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Start */}
      <div className="card bg-gradient-to-r from-scout-blue to-scout-light text-white">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold">Ready to start planning?</h3>
            <p className="opacity-90">Create your first term plan for the upcoming scouting year.</p>
          </div>
          <Link
            to="/term-planner"
            className="bg-white text-scout-blue px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center gap-2"
          >
            <Plus size={20} />
            New Term Plan
          </Link>
        </div>
      </div>
    </div>
  );
}